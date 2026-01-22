import pytest
from blog.models import Category, Content, ContentType


@pytest.mark.django_db
class TestContentTypeModel:
    def test_content_type_str_returns_name(self) -> None:
        content_type = ContentType.objects.create(
            name='Аудио',
            code='audio',
            upload_folder='audio',
        )
        assert str(content_type) == 'Аудио'

    def test_content_type_slug_auto_generated(self) -> None:
        content_type = ContentType.objects.create(
            name='Аудио',
            code='audio',
        )
        assert content_type.slug == 'аудио'

    def test_content_type_is_video(self, video_type: ContentType) -> None:
        assert video_type.is_video is True
        assert video_type.is_photo is False

    def test_content_type_is_photo(self, photo_type: ContentType) -> None:
        assert photo_type.is_photo is True
        assert photo_type.is_video is False


@pytest.mark.django_db
class TestContentModel:
    def test_content_str_returns_title(self, yoga_category: Category, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Утренняя йога',
            category=yoga_category,
            content_type=video_type,
        )
        assert str(content) == 'Утренняя йога'

    def test_content_default_category_is_none(self, video_type: ContentType) -> None:
        content = Content.objects.create(title='Тест', content_type=video_type)
        assert content.category is None

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
            category=yoga_category,
        )
        assert content.content_type.is_video is True

    def test_content_can_be_photo(self, yoga_category: Category, photo_type: ContentType) -> None:
        content = Content.objects.create(
            title='Фото йоги',
            content_type=photo_type,
            category=yoga_category,
        )
        assert content.content_type.is_photo is True

    def test_create_content_video(self, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Мое видео',
            description='Test Video',
            content_type=video_type,
        )
        assert content.description == 'Test Video'
        assert content.content_type.code == 'video'
        assert str(content) == 'Мое видео'

    def test_create_content_photo(self, photo_type: ContentType) -> None:
        content = Content.objects.create(
            title='Моя фотография',
            description='Test Photo',
            content_type=photo_type,
        )
        assert content.description == 'Test Photo'
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
