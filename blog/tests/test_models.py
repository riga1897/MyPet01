from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from blog.models import Category, Content


@pytest.mark.django_db
class TestContentModel:
    def test_content_str_returns_title(self, yoga_category: Category) -> None:
        content = Content.objects.create(title='Утренняя йога')
        content.categories.add(yoga_category)
        assert str(content) == 'Утренняя йога'

    def test_content_default_categories_is_empty(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.categories.count() == 0

    def test_content_default_type_is_video(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.content_type == 'video'

    def test_content_ordering_by_created_at_desc(self) -> None:
        c1 = Content.objects.create(title='Первое')
        c2 = Content.objects.create(title='Второе')
        contents = list(Content.objects.all())
        assert contents[0] == c2
        assert contents[1] == c1

    def test_content_type_choices(self) -> None:
        assert Content.ContentType.VIDEO.value == 'video'
        assert Content.ContentType.PHOTO.value == 'photo'

    def test_content_can_be_photo(self, yoga_category: Category) -> None:
        content = Content.objects.create(
            title='Фото йоги',
            content_type='photo',
        )
        content.categories.add(yoga_category)
        assert content.content_type == 'photo'

    def test_create_content_video(self) -> None:
        content = Content.objects.create(
            title='Мое видео',
            description='Test Video',
            content_type='video',
        )
        assert content.description == 'Test Video'
        assert content.content_type == 'video'
        assert str(content) == 'Мое видео'

    def test_create_content_photo(self) -> None:
        content = Content.objects.create(
            title='Моя фотография',
            description='Test Photo',
            content_type='photo',
        )
        assert content.description == 'Test Photo'
        assert content.content_type == 'photo'
        assert str(content) == 'Моя фотография'


@pytest.mark.django_db
class TestCategoryModel:
    def test_category_str_returns_name(self) -> None:
        category = Category.objects.create(
            name='Тестовая категория',
            code='test',
        )
        assert str(category) == 'Тестовая категория'

    def test_category_slug_auto_generated(self) -> None:
        category = Category.objects.create(
            name='Тестовая категория',
            code='test',
        )
        assert category.slug == 'тестовая-категория'

    def test_category_code_is_unique(self, yoga_category: Category) -> None:
        with pytest.raises(Exception):
            Category.objects.create(
                name='Другая категория',
                code='yoga',
            )


def _create_test_image(width: int = 100, height: int = 100, mode: str = 'RGB') -> bytes:
    """Create a test image in memory."""
    img = Image.new(mode, (width, height), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG' if mode == 'RGB' else 'PNG')
    buffer.seek(0)
    return buffer.read()


@pytest.mark.django_db
class TestContentThumbnailCompression:
    def test_compress_thumbnail_resizes_large_image(self) -> None:
        large_image = _create_test_image(1200, 900)
        thumbnail = SimpleUploadedFile('large.jpg', large_image, content_type='image/jpeg')
        content = Content.objects.create(
            title='Тест сжатия',
            content_type='photo',
            thumbnail=thumbnail,
        )
        assert content.thumbnail
        assert content.thumbnail.name.endswith('.jpg')

    def test_compress_thumbnail_converts_rgba_to_rgb(self) -> None:
        rgba_image = _create_test_image(100, 100, 'RGBA')
        thumbnail = SimpleUploadedFile('rgba.png', rgba_image, content_type='image/png')
        content = Content.objects.create(
            title='RGBA тест',
            content_type='photo',
            thumbnail=thumbnail,
        )
        assert content.thumbnail
        assert content.thumbnail.name.endswith('.jpg')

    def test_compress_thumbnail_handles_invalid_image(self) -> None:
        invalid_file = SimpleUploadedFile('bad.jpg', b'not an image', content_type='image/jpeg')
        content = Content.objects.create(
            title='Плохое изображение',
            content_type='photo',
            thumbnail=invalid_file,
        )
        assert content.pk is not None

    def test_compress_thumbnail_handles_os_error(self) -> None:
        image_data = _create_test_image()
        thumbnail = SimpleUploadedFile('test.jpg', image_data, content_type='image/jpeg')
        content = Content(title='OS Error', content_type='photo', thumbnail=thumbnail)
        with patch('blog.models.Image.open', side_effect=OSError('Disk full')):
            content.save()
        assert content.pk is not None


@pytest.mark.django_db
class TestContentAutoFields:
    def test_process_auto_fields_generates_duration_for_video(self) -> None:
        video_file = SimpleUploadedFile('test.mp4', b'video content', content_type='video/mp4')
        with patch('blog.models.get_video_duration', return_value='05:30'):
            with patch('blog.models.generate_thumbnail_from_video', return_value=None):
                content = Content.objects.create(
                    title='Видео тест',
                    content_type='video',
                    video_file=video_file,
                )
        assert content.duration == '05:30'

    def test_process_auto_fields_generates_thumbnail_for_video(self) -> None:
        video_file = SimpleUploadedFile('test.mp4', b'video content', content_type='video/mp4')
        fake_thumbnail = SimpleUploadedFile('thumb.jpg', _create_test_image(), content_type='image/jpeg')
        with patch('blog.models.get_video_duration', return_value=None):
            with patch('blog.models.generate_thumbnail_from_video', return_value=fake_thumbnail):
                content = Content.objects.create(
                    title='Видео тест',
                    content_type='video',
                    video_file=video_file,
                )
        assert content.thumbnail is not None

    def test_process_auto_fields_generates_thumbnail_for_photo(self) -> None:
        image_file = SimpleUploadedFile('photo.jpg', _create_test_image(), content_type='image/jpeg')
        fake_thumbnail = SimpleUploadedFile('thumb.jpg', _create_test_image(), content_type='image/jpeg')
        with patch('blog.models.generate_thumbnail_from_image', return_value=fake_thumbnail):
            content = Content.objects.create(
                title='Фото тест',
                content_type='photo',
                video_file=image_file,
            )
        assert content.thumbnail is not None

    def test_process_auto_fields_photo_thumbnail_none(self) -> None:
        image_file = SimpleUploadedFile('photo.jpg', _create_test_image(), content_type='image/jpeg')
        with patch('blog.models.generate_thumbnail_from_image', return_value=None):
            content = Content.objects.create(
                title='Фото без превью',
                content_type='photo',
                video_file=image_file,
            )
        assert content.pk is not None

    def test_is_new_thumbnail_returns_true_for_uploaded_file(self) -> None:
        image_data = _create_test_image()
        thumbnail = SimpleUploadedFile('new.jpg', image_data, content_type='image/jpeg')
        content = Content(title='Новое превью', content_type='photo', thumbnail=thumbnail)
        assert content._is_new_thumbnail() is True

    def test_has_playable_video_true(self) -> None:
        video_file = SimpleUploadedFile('test.mp4', b'video content', content_type='video/mp4')
        content = Content(title='Видео', content_type='video', video_file=video_file)
        assert content.has_playable_video() is True

    def test_has_playable_video_false_for_photo(self) -> None:
        video_file = SimpleUploadedFile('test.mp4', b'video content', content_type='video/mp4')
        content = Content(title='Фото', content_type='photo', video_file=video_file)
        assert content.has_playable_video() is False

    def test_compress_thumbnail_skips_empty_name(self) -> None:
        content = Content(title='Пустое имя', content_type='photo')
        content.thumbnail.name = ''
        content._compress_thumbnail()
        assert content.thumbnail.name == ''
