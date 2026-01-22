import pytest
from blog.models import Category, Content, ContentType, Tag, TagGroup


@pytest.mark.django_db
class TestContentModel:
    def test_content_str_returns_title(self, yoga_category: Category, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Утренняя йога',
            category=yoga_category,
        )
        content.content_types.add(video_type)
        assert str(content) == 'Утренняя йога'

    def test_content_default_category_is_none(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.category is None

    def test_content_default_type_is_none(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.content_types.count() == 0

    def test_content_ordering_by_created_at_desc(self, video_type: ContentType) -> None:
        c1 = Content.objects.create(title='Первое')
        c1.content_types.add(video_type)
        c2 = Content.objects.create(title='Второе')
        c2.content_types.add(video_type)
        contents = list(Content.objects.all())
        assert contents[0] == c2
        assert contents[1] == c1

    def test_content_can_be_video(self, yoga_category: Category, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Видео йоги',
            category=yoga_category,
        )
        content.content_types.add(video_type)
        assert content.content_types.count() == 1
        first_type = content.content_types.first()
        assert first_type is not None
        assert first_type.is_video is True

    def test_content_can_be_photo(self, yoga_category: Category, photo_type: ContentType) -> None:
        content = Content.objects.create(
            title='Фото йоги',
            category=yoga_category,
        )
        content.content_types.add(photo_type)
        assert content.content_types.count() == 1
        first_type = content.content_types.first()
        assert first_type is not None
        assert first_type.is_photo is True

    def test_create_content_video(self, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Мое видео',
            description='Test Video',
        )
        content.content_types.add(video_type)
        assert content.description == 'Test Video'
        assert content.content_types.count() == 1
        first_type = content.content_types.first()
        assert first_type is not None
        assert first_type.code == 'video'
        assert str(content) == 'Мое видео'

    def test_create_content_photo(self, photo_type: ContentType) -> None:
        content = Content.objects.create(
            title='Моя фотография',
            description='Test Photo',
        )
        content.content_types.add(photo_type)
        assert content.description == 'Test Photo'
        assert content.content_types.count() == 1
        first_type = content.content_types.first()
        assert first_type is not None
        assert first_type.code == 'photo'
        assert str(content) == 'Моя фотография'

    def test_content_can_have_multiple_types(self, video_type: ContentType, photo_type: ContentType) -> None:
        content = Content.objects.create(title='Мультимедиа')
        content.content_types.add(video_type, photo_type)
        assert content.content_types.count() == 2


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
            Category.objects.create(name='Другая категория', code='yoga')


@pytest.mark.django_db
class TestContentTypeModel:
    def test_content_type_str_returns_name(self) -> None:
        ct = ContentType.objects.create(name='Аудио', code='audio')
        assert str(ct) == 'Аудио'

    def test_upload_folder_auto_generated_from_code(self) -> None:
        ct = ContentType.objects.create(name='Тестовый тип', code='test')
        assert ct.upload_folder == 'test'

    def test_upload_folder_can_be_custom(self) -> None:
        ct = ContentType.objects.create(name='Аудио', code='audio', upload_folder='audio_files')
        assert ct.upload_folder == 'audio_files'

    def test_is_video_property(self, video_type: ContentType) -> None:
        assert video_type.is_video is True
        assert video_type.is_photo is False

    def test_is_photo_property(self, photo_type: ContentType) -> None:
        assert photo_type.is_photo is True
        assert photo_type.is_video is False


@pytest.mark.django_db
class TestTagGroupModel:
    def test_tag_group_str_returns_name(self) -> None:
        group = TagGroup.objects.create(name='Уровень сложности')
        assert str(group) == 'Уровень сложности'

    def test_tag_group_slug_auto_generated(self) -> None:
        group = TagGroup.objects.create(name='Уровень сложности')
        assert group.slug == 'уровень-сложности'


@pytest.mark.django_db
class TestTagModel:
    def test_tag_str_returns_name_with_group(self) -> None:
        group = TagGroup.objects.create(name='Уровень')
        tag = Tag.objects.create(name='Начинающий', group=group)
        assert str(tag) == 'Уровень: Начинающий'

    def test_tag_slug_auto_generated(self) -> None:
        group = TagGroup.objects.create(name='Уровень')
        tag = Tag.objects.create(name='Продвинутый', group=group)
        assert tag.slug == 'продвинутый'

    def test_tags_ordered_by_order_field(self) -> None:
        group = TagGroup.objects.create(name='Группа')
        tag1 = Tag.objects.create(name='Тег 1', group=group, order=2)
        tag2 = Tag.objects.create(name='Тег 2', group=group, order=1)
        tag3 = Tag.objects.create(name='Тег 3', group=group, order=3)
        tags = list(Tag.objects.filter(group=group))
        assert tags == [tag2, tag1, tag3]
