import pytest
from blog.models import Content


@pytest.mark.django_db
class TestContentModel:
    def test_content_str_returns_title(self) -> None:
        content = Content.objects.create(
            title='Утренняя йога',
            category='yoga',
        )
        assert str(content) == 'Утренняя йога'

    def test_content_default_category_is_yoga(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.category == 'yoga'

    def test_content_default_type_is_video(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.content_type == 'video'

    def test_content_ordering_by_created_at_desc(self) -> None:
        c1 = Content.objects.create(title='Первое')
        c2 = Content.objects.create(title='Второе')
        contents = list(Content.objects.all())
        assert contents[0] == c2
        assert contents[1] == c1

    def test_content_category_choices(self) -> None:
        assert Content.Category.YOGA.value == 'yoga'
        assert Content.Category.OILS.value == 'oils'

    def test_content_type_choices(self) -> None:
        assert Content.ContentType.VIDEO.value == 'video'
        assert Content.ContentType.PHOTO.value == 'photo'

    def test_content_can_be_photo(self) -> None:
        content = Content.objects.create(
            title='Фото йоги',
            content_type='photo',
            category='yoga',
        )
        assert content.content_type == 'photo'
