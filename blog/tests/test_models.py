import os
from io import BytesIO
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from blog.models import Category, Content, ContentType, Tag, TagGroup


@pytest.mark.django_db
class TestContentModel:
    def test_content_str_returns_title(self, yoga_category: Category, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Утренняя йога',
            content_type=video_type,
        )
        content.categories.add(yoga_category)
        assert str(content) == 'Утренняя йога'

    def test_content_default_category_is_none(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.categories.count() == 0

    def test_content_default_type_is_none(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.content_type is None

    def test_content_ordering_by_created_at_desc(self, video_type: ContentType) -> None:
        c1 = Content.objects.create(title='Первое', content_type=video_type)
        c2 = Content.objects.create(title='Второе', content_type=video_type)
        contents = list(Content.objects.all())
        assert contents[0] == c2
        assert contents[1] == c1

    def test_content_can_be_video(self, yoga_category: Category, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Видео йоги',
            content_type=video_type,
        )
        content.categories.add(yoga_category)
        assert content.content_type is not None
        assert content.content_type.is_video is True

    def test_content_can_be_photo(self, yoga_category: Category, photo_type: ContentType) -> None:
        content = Content.objects.create(
            title='Фото йоги',
            content_type=photo_type,
        )
        content.categories.add(yoga_category)
        assert content.content_type is not None
        assert content.content_type.is_photo is True

    def test_create_content_video(self, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Мое видео',
            description='Test Video',
            content_type=video_type,
        )
        assert content.description == 'Test Video'
        assert content.content_type is not None
        assert content.content_type.code == 'video'
        assert str(content) == 'Мое видео'

    def test_create_content_photo(self, photo_type: ContentType) -> None:
        content = Content.objects.create(
            title='Моя фотография',
            description='Test Photo',
            content_type=photo_type,
        )
        assert content.description == 'Test Photo'
        assert content.content_type is not None
        assert content.content_type.code == 'photo'
        assert str(content) == 'Моя фотография'


@pytest.mark.django_db
class TestCategoryModel:
    def test_category_str_returns_name(self) -> None:
        category = Category.objects.create(
            name='Тестовая категория',
            code='test',
        )
        assert str(category) == 'Тестовая категория'

    def test_category_code_is_unique(self) -> None:
        from django.db import IntegrityError
        Category.objects.create(name='Категория 1', code='cat1')
        with pytest.raises(IntegrityError):
            Category.objects.create(name='Категория 2', code='cat1')


@pytest.mark.django_db
class TestTagGroupModel:
    def test_taggroup_str_returns_name(self) -> None:
        group = TagGroup.objects.create(name='Тестовая группа')
        assert str(group) == 'Тестовая группа'

    def test_taggroup_is_visible_for_category_when_empty(self, yoga_category: Category) -> None:
        group = TagGroup.objects.create(name='Универсальная группа')
        assert group.is_visible_for_category(yoga_category) is True

    def test_taggroup_is_visible_for_category_when_linked(
        self, yoga_category: Category, oils_category: Category
    ) -> None:
        group = TagGroup.objects.create(name='Только йога')
        group.categories.add(yoga_category)
        assert group.is_visible_for_category(yoga_category) is True
        assert group.is_visible_for_category(oils_category) is False

    def test_taggroup_is_visible_for_category_none(self) -> None:
        group = TagGroup.objects.create(name='Группа тест')
        assert group.is_visible_for_category(None) is True
        group.categories.add(Category.objects.create(name='Cat тест', code='cat_test'))
        assert group.is_visible_for_category(None) is False

    def test_taggroup_category_pks_empty(self) -> None:
        """category_pks returns empty set when no categories linked."""
        group = TagGroup.objects.create(name='Универсальная')
        assert group.category_pks == set()

    def test_taggroup_category_pks_with_categories(
        self, yoga_category: Category, oils_category: Category
    ) -> None:
        """category_pks returns set of linked category PKs."""
        group = TagGroup.objects.create(name='С категориями')
        group.categories.add(yoga_category, oils_category)
        assert group.category_pks == {yoga_category.pk, oils_category.pk}

    def test_taggroup_is_visible_uses_prefetch(
        self, yoga_category: Category, oils_category: Category
    ) -> None:
        """is_visible_for_category works correctly with prefetched data."""
        group = TagGroup.objects.create(name='Prefetch test')
        group.categories.add(yoga_category)
        prefetched_group = TagGroup.objects.prefetch_related('categories').get(pk=group.pk)
        assert prefetched_group.is_visible_for_category(yoga_category) is True
        assert prefetched_group.is_visible_for_category(oils_category) is False


@pytest.mark.django_db
class TestTagModel:
    def test_tag_str_returns_group_and_name(self) -> None:
        group = TagGroup.objects.create(name='Месяц')
        tag = Tag.objects.create(name='Первый', group=group)
        assert str(tag) == 'Месяц: Первый'

    def test_tag_ordering(self) -> None:
        group = TagGroup.objects.create(name='Группа')
        t1 = Tag.objects.create(name='Второй', group=group, order=2)
        t2 = Tag.objects.create(name='Первый', group=group, order=1)
        tags = list(Tag.objects.all())
        assert tags[0] == t2
        assert tags[1] == t1


@pytest.mark.django_db
class TestContentTypeModel:
    def test_contenttype_str_returns_name(self, video_type: ContentType) -> None:
        assert str(video_type) == 'Видео'

    def test_contenttype_is_video_property(self, video_type: ContentType) -> None:
        assert video_type.is_video is True
        assert video_type.is_photo is False

    def test_contenttype_is_photo_property(self, photo_type: ContentType) -> None:
        assert photo_type.is_photo is True
        assert photo_type.is_video is False

    def test_contenttype_code_is_required(self) -> None:
        from django.core.exceptions import ValidationError
        ct = ContentType(name='Без кода тест')
        with pytest.raises(ValidationError):
            ct.full_clean()

    def test_contenttype_code_is_unique(self) -> None:
        from django.db import IntegrityError
        ContentType.objects.create(name='Уникальный тип 1', code='unique_type1')
        with pytest.raises(IntegrityError):
            ContentType.objects.create(name='Уникальный тип 2', code='unique_type1')

    def test_contenttype_upload_folder_defaults_to_code(self) -> None:
        ct = ContentType.objects.create(name='Аудио тест', code='audio_test')
        assert ct.upload_folder == 'audio_test'

    def test_contenttype_upload_folder_custom(self) -> None:
        ct = ContentType.objects.create(name='Документы тест', code='docs_test', upload_folder='documents')
        assert ct.upload_folder == 'documents'

    def test_contenttype_has_related_content_false_when_empty(self) -> None:
        ct = ContentType.objects.create(name='Пустой тип', code='empty_type')
        assert ct.has_related_content() is False
        assert ct.get_related_content_count() == 0

    def test_contenttype_has_related_content_true_when_content_exists(
        self, video_type: ContentType
    ) -> None:
        Content.objects.create(title='Тест', content_type=video_type)
        assert video_type.has_related_content() is True
        assert video_type.get_related_content_count() == 1

    def test_contenttype_delete_without_content_succeeds(self) -> None:
        ct = ContentType.objects.create(name='Удаляемый', code='deletable')
        ct_id = ct.id
        ct.delete()
        assert not ContentType.objects.filter(id=ct_id).exists()

    def test_contenttype_delete_with_content_raises_error(
        self, video_type: ContentType
    ) -> None:
        Content.objects.create(title='Тест', content_type=video_type)
        with pytest.raises(ValueError, match='Невозможно удалить'):
            video_type.delete()


@pytest.mark.django_db
class TestContentFileUploadPath:
    """Tests for content_file_upload_path function."""

    def test_uses_upload_folder_from_content_type(self, video_type: ContentType) -> None:
        from blog.models import content_file_upload_path
        content = Content(content_type=video_type, title='Тест')
        path = content_file_upload_path(content, 'test_video.mp4')
        assert path == 'videos/test_video.mp4'

    def test_fallback_to_content_folder_when_no_type(self) -> None:
        from blog.models import content_file_upload_path
        content = Content(title='Без типа')
        path = content_file_upload_path(content, 'test_file.mp4')
        assert path == 'content/test_file.mp4'

    def test_fallback_to_content_folder_when_no_upload_folder(self) -> None:
        from blog.models import content_file_upload_path
        ct = ContentType(name='Без папки', code='no_folder', upload_folder='')
        content = Content(content_type=ct, title='Тест')
        path = content_file_upload_path(content, 'file.mp4')
        assert path == 'content/file.mp4'


@pytest.mark.django_db
class TestTagGroupCategoryPks:
    """Tests for TagGroup.category_pks property."""

    def test_category_pks_returns_empty_set_for_no_categories(self) -> None:
        tg = TagGroup.objects.create(name='Без категорий')
        assert tg.category_pks == set()

    def test_category_pks_returns_category_pks(
        self, yoga_category: Category
    ) -> None:
        tg = TagGroup.objects.create(name='С категорией')
        tg.categories.add(yoga_category)
        assert tg.category_pks == {yoga_category.pk}


@pytest.mark.django_db
class TestContentThumbnailCompression:
    """Tests for Content thumbnail compression."""

    def _create_test_image(self, width: int = 800, height: int = 600, mode: str = 'RGB') -> BytesIO:
        """Create a test image in memory."""
        img = Image.new(mode, (width, height), color='blue')
        buffer = BytesIO()
        fmt = 'PNG' if mode == 'RGBA' else 'JPEG'
        img.save(buffer, format=fmt)
        buffer.seek(0)
        return buffer

    def test_compress_thumbnail_rgb_image(self, video_type: ContentType) -> None:
        """Test compression of RGB image."""
        img_buffer = self._create_test_image()
        uploaded = SimpleUploadedFile('test.jpg', img_buffer.read(), content_type='image/jpeg')
        content = Content(title='Тест', content_type=video_type, thumbnail=uploaded)
        content._compress_thumbnail()
        assert content.thumbnail.name.endswith('.jpg')

    def test_compress_thumbnail_rgba_image(self, video_type: ContentType) -> None:
        """Test compression of RGBA image converts to RGB."""
        img_buffer = self._create_test_image(mode='RGBA')
        uploaded = SimpleUploadedFile('test.png', img_buffer.read(), content_type='image/png')
        content = Content(title='Тест', content_type=video_type, thumbnail=uploaded)
        content._compress_thumbnail()
        assert content.thumbnail.name.endswith('.jpg')

    def test_compress_thumbnail_invalid_image_logs_warning(
        self, video_type: ContentType
    ) -> None:
        """Test that invalid image logs warning."""
        uploaded = SimpleUploadedFile('bad.jpg', b'not an image', content_type='image/jpeg')
        content = Content(title='Тест', content_type=video_type, thumbnail=uploaded)
        with patch('blog.models.logger') as mock_logger:
            content._compress_thumbnail()
            mock_logger.warning.assert_called()

    def test_compress_thumbnail_empty_name_returns_early(
        self, video_type: ContentType
    ) -> None:
        """Test that empty thumbnail name returns early."""
        content = Content(title='Тест', content_type=video_type)
        content._compress_thumbnail()


@pytest.mark.django_db
class TestContentAutoThumbnail:
    """Tests for Content auto-thumbnail generation."""

    def test_process_auto_fields_video_generates_thumbnail(
        self, video_type: ContentType
    ) -> None:
        """Test auto-thumbnail generation for video content."""
        folder = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder, exist_ok=True)
        video_path = os.path.join(folder, 'test_auto.mp4')
        with open(video_path, 'wb') as f:
            f.write(b'fake video content')
        try:
            content = Content.objects.create(
                title='Видео',
                content_type=video_type,
            )
            Content.objects.filter(pk=content.pk).update(video_file='videos/test_auto.mp4')
            content.refresh_from_db()
            with patch('blog.models.generate_thumbnail_from_video') as mock_gen:
                mock_gen.return_value = 'thumbnails/generated.jpg'
                content._process_auto_fields_after_save()
                mock_gen.assert_called_once()
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)

    def test_process_auto_fields_photo_generates_thumbnail(
        self, photo_type: ContentType
    ) -> None:
        """Test auto-thumbnail generation for photo content."""
        folder = os.path.join(settings.MEDIA_ROOT, 'photos')
        os.makedirs(folder, exist_ok=True)
        with patch('blog.models.generate_thumbnail_from_image') as mock_gen:
            mock_gen.return_value = 'thumbnails/photo_thumb.jpg'
            content = Content.objects.create(
                title='Фото',
                content_type=photo_type,
            )
            Content.objects.filter(pk=content.pk).update(video_file='photos/test.jpg')
            content.refresh_from_db()
            content._process_auto_fields_after_save()
            mock_gen.assert_called_once()


@pytest.mark.django_db
class TestContentDelete:
    """Tests for Content delete method."""

    def test_delete_removes_thumbnail_file(self, video_type: ContentType) -> None:
        """Test that deleting content removes the thumbnail file."""
        thumbs_folder = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbs_folder, exist_ok=True)
        thumb_path = os.path.join(thumbs_folder, 'to_delete.jpg')
        with open(thumb_path, 'w') as f:
            f.write('test')
        try:
            content = Content.objects.create(title='Удаляемый', content_type=video_type)
            Content.objects.filter(pk=content.pk).update(thumbnail='thumbnails/to_delete.jpg')
            content.refresh_from_db()
            content.delete()
            assert not os.path.exists(thumb_path)
        finally:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)

    def test_delete_without_thumbnail_succeeds(self, video_type: ContentType) -> None:
        """Test that deleting content without thumbnail works."""
        content = Content.objects.create(title='Без thumb', content_type=video_type)
        content.delete()
        assert not Content.objects.filter(pk=content.pk).exists()


@pytest.mark.django_db
class TestContentThumbnailEdgeCases:
    """Tests for thumbnail edge cases (covers lines 265, 325-326)."""

    def test_compress_thumbnail_with_invalid_image(
        self, video_type: ContentType
    ) -> None:
        """Test thumbnail compression with invalid image file (line 325-326)."""
        content = Content.objects.create(
            title='Invalid Thumb Test',
            content_type=video_type,
        )
        invalid_file = SimpleUploadedFile(
            name='invalid.jpg',
            content=b'not an image content',
            content_type='image/jpeg',
        )
        content.thumbnail = invalid_file
        content.save()
        assert content.pk is not None

    def test_save_triggers_thumbnail_compression(
        self, video_type: ContentType
    ) -> None:
        """Test save with new thumbnail triggers compression (line 265)."""
        img_io = BytesIO()
        img = Image.new('RGB', (200, 200), color='blue')
        img.save(img_io, format='JPEG')
        img_io.seek(0)
        
        content = Content.objects.create(
            title='Compression Test',
            content_type=video_type,
        )
        thumb_file = SimpleUploadedFile(
            name='compress_test.jpg',
            content=img_io.read(),
            content_type='image/jpeg',
        )
        content.thumbnail = thumb_file
        content.save()
        
        if content.thumbnail:
            thumb_path = os.path.join(settings.MEDIA_ROOT, str(content.thumbnail))
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
