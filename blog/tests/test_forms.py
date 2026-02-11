import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from blog.forms import ContentForm, MAX_FILE_SIZE_MB, validate_file_size
from blog.models import Category, ContentType


class TestContentForm:
    def test_form_has_all_fields(self) -> None:
        form = ContentForm()
        assert 'title' in form.fields
        assert 'description' in form.fields
        assert 'content_type' in form.fields
        assert 'categories' in form.fields
        assert 'thumbnail' in form.fields
        assert 'video_file' in form.fields

    def test_form_labels_in_russian(self) -> None:
        form = ContentForm()
        assert form.fields['title'].label == 'Заголовок'
        assert form.fields['description'].label == 'Описание'
        assert form.fields['content_type'].label == 'Тип контента'
        assert form.fields['categories'].label == 'Категории'

    @pytest.mark.django_db
    def test_valid_form_creates_content(self, yoga_category: Category, video_type: ContentType) -> None:
        form = ContentForm(data={
            'title': 'Тестовый контент',
            'description': 'Описание',
            'content_type': video_type.pk,
            'categories': [yoga_category.pk],
        })
        assert form.is_valid(), form.errors
        content = form.save()
        assert content.title == 'Тестовый контент'
        assert content.content_type == video_type

    @pytest.mark.django_db
    def test_valid_form_without_content_type(self, yoga_category: Category) -> None:
        form = ContentForm(data={
            'title': 'Контент без типа',
            'description': 'Описание',
            'categories': [yoga_category.pk],
        })
        assert form.is_valid(), form.errors
        content = form.save()
        assert content.content_type is None

    def test_title_is_required(self) -> None:
        form = ContentForm(data={
            'description': 'Описание',
        })
        assert not form.is_valid()
        assert 'title' in form.errors

    @pytest.mark.django_db
    def test_save_adds_hash_to_uploaded_file(
        self, yoga_category: Category, video_type: ContentType
    ) -> None:
        """When saving with uploaded file, filename should get MD5 hash."""
        file_content = b'test video content for hashing'
        uploaded_file = SimpleUploadedFile('my_video.mp4', file_content)
        
        from django.utils.datastructures import MultiValueDict
        form = ContentForm(
            data={
                'title': 'Видео с хэшем',
                'description': 'Тест',
                'content_type': video_type.pk,
                'categories': [yoga_category.pk],
            },
            files=MultiValueDict({'video_file': [uploaded_file]})
        )
        assert form.is_valid(), form.errors
        content = form.save()
        
        assert content.video_file.name is not None
        filename = content.video_file.name.split('/')[-1]
        assert filename.startswith('my_video_')
        assert filename.endswith('.mp4')
        assert len(filename) > len('my_video_.mp4')

    @pytest.mark.django_db
    def test_save_without_file_works(self, yoga_category: Category) -> None:
        """Saving without file should work normally."""
        form = ContentForm(data={
            'title': 'Контент без файла',
            'description': 'Описание',
            'categories': [yoga_category.pk],
        })
        assert form.is_valid(), form.errors
        content = form.save()
        
        assert content.pk is not None
        assert content.title == 'Контент без файла'
        assert not content.video_file


class TestValidateFileSize:
    """Tests for validate_file_size function."""

    def test_accepts_file_within_limit(self) -> None:
        """Should not raise for files within size limit."""
        small_file = SimpleUploadedFile('small.mp4', b'x' * 1024)
        validate_file_size(small_file, 'Файл')

    def test_rejects_file_exceeding_limit(self) -> None:
        """Should raise ValidationError for files exceeding size limit."""
        from unittest.mock import MagicMock
        
        large_file = MagicMock()
        large_file.size = (MAX_FILE_SIZE_MB + 1) * 1024 * 1024
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(large_file, 'Файл')
        
        assert 'файл слишком большой' in str(exc_info.value)
        assert str(MAX_FILE_SIZE_MB) in str(exc_info.value)

    def test_accepts_none_file(self) -> None:
        """Should not raise for None file."""
        validate_file_size(None, 'Файл')

    def test_accepts_file_without_size_attribute(self) -> None:
        """Should not raise for file without size attribute."""
        from unittest.mock import MagicMock
        
        file_no_size = MagicMock(spec=[])
        validate_file_size(file_no_size, 'Файл')

    def test_accepts_file_with_none_size(self) -> None:
        """Should not raise for file with None size."""
        from unittest.mock import MagicMock
        
        file_none_size = MagicMock()
        file_none_size.size = None
        validate_file_size(file_none_size, 'Файл')


class TestContentFormFileSizeValidation:
    """Integration tests for file size validation in ContentForm."""

    @pytest.mark.django_db
    def test_clean_video_file_rejects_oversized_file(
        self, yoga_category: Category, video_type: ContentType
    ) -> None:
        """clean_video_file should reject files exceeding size limit."""
        from unittest.mock import patch
        
        small_video = SimpleUploadedFile(
            'test.mp4', b'x' * 100, content_type='video/mp4'
        )
        oversized_bytes = (MAX_FILE_SIZE_MB + 1) * 1024 * 1024
        
        with patch.object(small_video, 'size', oversized_bytes):
            form = ContentForm(
                data={
                    'title': 'Тест',
                    'description': 'Описание',
                    'content_type': video_type.pk,
                    'categories': [yoga_category.pk],
                },
                files={'video_file': small_video}  # type: ignore[arg-type]
            )
            
            assert not form.is_valid()
            assert 'video_file' in form.errors
            assert 'слишком большой' in str(form.errors['video_file'])

    @pytest.mark.django_db
    def test_clean_thumbnail_rejects_oversized_file(
        self, yoga_category: Category
    ) -> None:
        """clean_thumbnail should reject files exceeding size limit."""
        from unittest.mock import patch
        import io
        from PIL import Image
        
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        valid_image = SimpleUploadedFile(
            'test.jpg', img_io.read(), content_type='image/jpeg'
        )
        oversized_bytes = (MAX_FILE_SIZE_MB + 1) * 1024 * 1024
        
        with patch.object(valid_image, 'size', oversized_bytes):
            form = ContentForm(
                data={
                    'title': 'Тест',
                    'description': 'Описание',
                    'categories': [yoga_category.pk],
                },
                files={'thumbnail': valid_image}  # type: ignore[arg-type]
            )
            
            assert not form.is_valid()
            assert 'thumbnail' in form.errors
            assert 'слишком большой' in str(form.errors['thumbnail'])
