import pytest
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
