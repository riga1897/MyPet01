"""Tests for blog services (video processing, thumbnail generation)."""
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from django.core.files.uploadedfile import SimpleUploadedFile

from blog.services import (
    generate_hashed_filename,
    generate_thumbnail_from_image,
    generate_thumbnail_from_video,
)


class TestGenerateThumbnailFromVideo:
    """Tests for generate_thumbnail_from_video function."""

    def test_returns_none_when_no_file(self) -> None:
        """Should return None when video_file is None."""
        assert generate_thumbnail_from_video(None) is None

    def test_returns_none_when_no_path_attribute(self) -> None:
        """Should return None when video_file has no path attribute."""
        mock_file = MagicMock(spec=[])
        assert generate_thumbnail_from_video(mock_file) is None

    @patch('blog.services.subprocess.run')
    @patch('blog.services.Path')
    def test_returns_none_on_ffmpeg_failure(
        self, mock_path_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """Should return None when ffmpeg fails."""
        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_path_instance = MagicMock()
        mock_path_instance.stat.return_value = mock_stat
        mock_path_instance.exists.return_value = False
        mock_path_cls.return_value = mock_path_instance

        mock_run.return_value = MagicMock(returncode=1)
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        result = generate_thumbnail_from_video(mock_file)

        assert result is None

    @patch('blog.services.subprocess.run')
    @patch('blog.services.Path')
    def test_returns_content_file_on_success(
        self, mock_path_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """Should return ContentFile when ffmpeg succeeds."""
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = BytesIO()
        img.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_path_instance = MagicMock()
        mock_path_instance.stat.return_value = mock_stat
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_bytes.return_value = img_bytes
        mock_path_instance.unlink = MagicMock()
        mock_path_cls.return_value = mock_path_instance

        mock_run.return_value = MagicMock(returncode=0)
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        with patch('blog.services.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = tmp_path
            result = generate_thumbnail_from_video(mock_file)

        assert result is not None
        assert result.name is not None
        assert result.name.startswith('video_')
        assert result.name.endswith('.jpg')
        
        Path(tmp_path).unlink(missing_ok=True)


class TestGenerateThumbnailFromImage:
    """Tests for generate_thumbnail_from_image function."""

    def test_returns_none_when_no_file(self) -> None:
        """Should return None when image_file is None."""
        assert generate_thumbnail_from_image(None) is None

    def test_returns_content_file_for_valid_image(self) -> None:
        """Should return ContentFile for valid image."""
        img = Image.new('RGB', (1000, 1000), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)

        result = generate_thumbnail_from_image(buffer)

        assert result is not None
        assert result.name is not None
        assert result.name.startswith('photo_')
        assert result.name.endswith('.jpg')
        assert len(result.read()) > 0

    def test_handles_rgba_images(self) -> None:
        """Should convert RGBA images to RGB."""
        img = Image.new('RGBA', (500, 500), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        result = generate_thumbnail_from_image(buffer)

        assert result is not None
        assert result.name is not None
        assert result.name.startswith('photo_')
        assert result.name.endswith('.jpg')

    def test_returns_none_for_invalid_file(self) -> None:
        """Should return None for non-image file."""
        buffer = BytesIO(b'not an image')

        result = generate_thumbnail_from_image(buffer)

        assert result is None

    def test_resizes_large_images(self) -> None:
        """Should resize images larger than max size."""
        img = Image.new('RGB', (2000, 1500), color='green')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)

        result = generate_thumbnail_from_image(buffer)

        assert result is not None
        result_buffer = BytesIO(result.read())
        result_img = Image.open(result_buffer)
        assert result_img.size[0] <= 800
        assert result_img.size[1] <= 600


class TestGenerateHashedFilename:
    """Tests for generate_hashed_filename function."""

    def test_generates_hash_from_content(self) -> None:
        """Should generate filename with hash from content."""
        content = b'test file content'
        uploaded_file = SimpleUploadedFile('photo.jpg', content)
        
        hashed_name, content_hash = generate_hashed_filename(uploaded_file)
        
        assert content_hash in hashed_name
        assert hashed_name.endswith('.jpg')
        assert hashed_name.startswith('photo_')
        assert len(content_hash) == 8

    def test_same_content_produces_same_hash(self) -> None:
        """Same content should produce same hash regardless of filename."""
        content = b'identical content'
        file1 = SimpleUploadedFile('file1.png', content)
        file2 = SimpleUploadedFile('file2.png', content)
        
        _, hash1 = generate_hashed_filename(file1)
        _, hash2 = generate_hashed_filename(file2)
        
        assert hash1 == hash2

    def test_different_content_produces_different_hash(self) -> None:
        """Different content should produce different hash."""
        file1 = SimpleUploadedFile('test.jpg', b'content 1')
        file2 = SimpleUploadedFile('test.jpg', b'content 2')
        
        _, hash1 = generate_hashed_filename(file1)
        _, hash2 = generate_hashed_filename(file2)
        
        assert hash1 != hash2

    def test_preserves_file_extension(self) -> None:
        """Should preserve original file extension."""
        file_mp4 = SimpleUploadedFile('video.mp4', b'video data')
        file_png = SimpleUploadedFile('image.png', b'image data')
        
        name_mp4, _ = generate_hashed_filename(file_mp4)
        name_png, _ = generate_hashed_filename(file_png)
        
        assert name_mp4.endswith('.mp4')
        assert name_png.endswith('.png')

    def test_file_position_reset_after_hashing(self) -> None:
        """Should reset file position after hashing for further processing."""
        content = b'test content for position check'
        uploaded_file = SimpleUploadedFile('test.txt', content)
        
        generate_hashed_filename(uploaded_file)
        
        uploaded_file.seek(0)
        assert uploaded_file.read() == content


class TestGenerateThumbnailFromVideoEdgeCases:
    """Edge case tests for generate_thumbnail_from_video."""

    @patch('blog.services.subprocess.run')
    @patch('blog.services.Path')
    def test_converts_rgba_to_rgb(
        self, mock_path_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """Should convert RGBA image from ffmpeg to RGB."""
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_path_instance = MagicMock()
        mock_path_instance.stat.return_value = mock_stat
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_bytes.return_value = img_bytes
        mock_path_instance.unlink = MagicMock()
        mock_path_cls.return_value = mock_path_instance

        mock_run.return_value = MagicMock(returncode=0)
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        with patch('blog.services.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = tmp_path
            result = generate_thumbnail_from_video(mock_file)

        assert result is not None
        Path(tmp_path).unlink(missing_ok=True)

    @patch('blog.services.subprocess.run')
    @patch('blog.services.Path')
    def test_returns_none_on_timeout(
        self, mock_path_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """Should return None and cleanup on subprocess timeout."""
        import subprocess

        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_path_instance = MagicMock()
        mock_path_instance.stat.return_value = mock_stat
        mock_path_instance.unlink = MagicMock()
        mock_path_cls.return_value = mock_path_instance

        mock_run.side_effect = subprocess.TimeoutExpired('ffmpeg', 30)
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        with patch('blog.services.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = tmp_path
            result = generate_thumbnail_from_video(mock_file)

        assert result is None
        Path(tmp_path).unlink(missing_ok=True)

    @patch('blog.services.subprocess.run')
    @patch('blog.services.Path')
    def test_returns_none_on_oserror(
        self, mock_path_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """Should return None on OSError from subprocess."""
        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_path_instance = MagicMock()
        mock_path_instance.stat.return_value = mock_stat
        mock_path_instance.unlink = MagicMock()
        mock_path_cls.return_value = mock_path_instance

        mock_run.side_effect = OSError("ffmpeg not found")
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        with patch('blog.services.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = tmp_path
            result = generate_thumbnail_from_video(mock_file)

        assert result is None
        Path(tmp_path).unlink(missing_ok=True)

    @patch('blog.services.subprocess.run')
    @patch('blog.services.Path')
    def test_cleanup_tmp_file_after_success(
        self, mock_path_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """Should remove temp file after successful processing."""
        img = Image.new('RGB', (100, 100), color='green')
        img_buffer = BytesIO()
        img.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name

        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_path_instance = MagicMock()
        mock_path_instance.stat.return_value = mock_stat
        mock_path_instance.exists.return_value = True
        mock_path_instance.read_bytes.return_value = img_bytes
        mock_path_instance.unlink = MagicMock()
        mock_path_cls.return_value = mock_path_instance

        mock_run.return_value = MagicMock(returncode=0)
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        with patch('blog.services.tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = tmp_path
            result = generate_thumbnail_from_video(mock_file)

        assert result is not None
        Path(tmp_path).unlink(missing_ok=True)


class TestVideoFileSizeValidation:
    """Tests for video file size validation in generate_thumbnail_from_video."""

    @patch('blog.services.Path')
    def test_returns_none_when_file_too_large(self, mock_path_cls: MagicMock) -> None:
        """Should return None when video file exceeds MAX_VIDEO_SIZE_BYTES."""
        from blog.services import MAX_VIDEO_SIZE_BYTES

        mock_stat = MagicMock()
        mock_stat.st_size = MAX_VIDEO_SIZE_BYTES + 1
        mock_path_instance = MagicMock()
        mock_path_instance.stat.return_value = mock_stat
        mock_path_cls.return_value = mock_path_instance

        mock_file = MagicMock()
        mock_file.path = '/path/to/large_video.mp4'

        result = generate_thumbnail_from_video(mock_file)

        assert result is None

    @patch('blog.services.Path')
    def test_returns_none_on_stat_oserror(self, mock_path_cls: MagicMock) -> None:
        """Should return None when stat() raises OSError."""
        mock_path_instance = MagicMock()
        mock_path_instance.stat.side_effect = OSError("File not found")
        mock_path_cls.return_value = mock_path_instance

        mock_file = MagicMock()
        mock_file.path = '/path/to/nonexistent.mp4'

        result = generate_thumbnail_from_video(mock_file)

        assert result is None

    @patch('blog.services.subprocess.run')
    @patch('blog.services.Path')
    def test_proceeds_when_file_size_ok(
        self, mock_path_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """Should proceed to ffmpeg when file size is within limits."""
        from blog.services import MAX_VIDEO_SIZE_BYTES

        mock_stat = MagicMock()
        mock_stat.st_size = MAX_VIDEO_SIZE_BYTES - 1
        mock_path_instance = MagicMock()
        mock_path_instance.stat.return_value = mock_stat
        mock_path_instance.exists.return_value = False
        mock_path_cls.return_value = mock_path_instance

        mock_run.return_value = MagicMock(returncode=1)
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        generate_thumbnail_from_video(mock_file)

        mock_run.assert_called_once()


class TestThumbnailTempFileCleanup:
    """Tests for temp file cleanup (covers lines 96-97)."""

    @patch('blog.services.subprocess.run')
    @patch('blog.services.tempfile.NamedTemporaryFile')
    @patch('blog.services.Image')
    @patch('blog.services.Path')
    def test_cleanup_temp_file_after_success(
        self,
        mock_path_cls: MagicMock,
        mock_image: MagicMock,
        mock_tempfile: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """Test temp file is deleted after successful thumbnail generation."""
        mock_stat = MagicMock()
        mock_stat.st_size = 1024

        mock_tmp_file = MagicMock()
        mock_tmp_file.name = '/tmp/test.jpg'
        mock_tmp_file.__enter__ = MagicMock(return_value=mock_tmp_file)
        mock_tmp_file.__exit__ = MagicMock(return_value=False)
        mock_tempfile.return_value = mock_tmp_file

        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.stat.return_value = mock_stat
        mock_path_instance.read_bytes.return_value = b'fake_jpg_data'
        mock_path_cls.return_value = mock_path_instance

        mock_run.return_value = MagicMock(returncode=0)

        mock_pil_image = MagicMock()
        mock_pil_image.mode = 'RGB'
        mock_image.open.return_value = mock_pil_image

        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        with patch('blog.services.ContentFile'), patch('blog.services.BytesIO'):
            generate_thumbnail_from_video(mock_file)

        mock_path_instance.unlink.assert_called()
