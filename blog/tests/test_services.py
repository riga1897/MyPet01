"""Tests for blog services (video processing, thumbnail generation)."""
import tempfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from blog.services import (
    generate_thumbnail_from_image,
    generate_thumbnail_from_video,
    get_video_duration,
)


class TestGetVideoDuration:
    """Tests for get_video_duration function."""

    def test_returns_empty_string_when_no_file(self) -> None:
        """Should return empty string when video_file is None."""
        assert get_video_duration(None) == ''

    def test_returns_empty_string_when_no_path_attribute(self) -> None:
        """Should return empty string when video_file has no path attribute."""
        mock_file = MagicMock(spec=[])
        assert get_video_duration(mock_file) == ''

    @patch('blog.services.subprocess.run')
    def test_returns_formatted_duration_on_success(
        self, mock_run: MagicMock
    ) -> None:
        """Should return MM:SS format when ffprobe succeeds."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='125.5\n',
        )
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        result = get_video_duration(mock_file)

        assert result == '2:05'
        mock_run.assert_called_once()

    @patch('blog.services.subprocess.run')
    def test_returns_empty_string_on_ffprobe_failure(
        self, mock_run: MagicMock
    ) -> None:
        """Should return empty string when ffprobe fails."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
        )
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        result = get_video_duration(mock_file)

        assert result == ''

    @patch('blog.services.subprocess.run')
    def test_handles_timeout(self, mock_run: MagicMock) -> None:
        """Should return empty string on timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('ffprobe', 30)
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        result = get_video_duration(mock_file)

        assert result == ''


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
    def test_returns_none_on_ffmpeg_failure(
        self, mock_run: MagicMock
    ) -> None:
        """Should return None when ffmpeg fails."""
        mock_run.return_value = MagicMock(returncode=1)
        mock_file = MagicMock()
        mock_file.path = '/path/to/video.mp4'

        result = generate_thumbnail_from_video(mock_file)

        assert result is None

    @patch('blog.services.subprocess.run')
    def test_returns_content_file_on_success(
        self, mock_run: MagicMock
    ) -> None:
        """Should return ContentFile when ffmpeg succeeds."""
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = BytesIO()
        img.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        def mock_ffmpeg(*args: object, **kwargs: object) -> MagicMock:
            Path(tmp_path).write_bytes(img_bytes)
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_ffmpeg
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
