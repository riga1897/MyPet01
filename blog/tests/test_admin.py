import pytest
from django.contrib.admin.sites import AdminSite
from blog.admin import CategoryAdmin, ContentAdmin, TagGroupAdmin
from blog.models import Category, Content, TagGroup


@pytest.mark.django_db
class TestTagGroupAdmin:
    def test_get_categories_returns_all_when_empty(self) -> None:
        tag_group = TagGroup.objects.create(name='Тестовая группа')
        admin = TagGroupAdmin(TagGroup, AdminSite())
        assert admin.get_categories(tag_group) == 'Все'

    def test_get_categories_returns_names_when_set(
        self, yoga_category: Category, oils_category: Category
    ) -> None:
        tag_group = TagGroup.objects.create(name='Тестовая группа')
        tag_group.categories.add(yoga_category, oils_category)
        admin = TagGroupAdmin(TagGroup, AdminSite())
        result = admin.get_categories(tag_group)
        assert 'Йога' in result
        assert 'Эфирные масла' in result


@pytest.mark.django_db
class TestContentAdmin:
    def test_get_categories_returns_all_when_empty(self) -> None:
        content = Content.objects.create(title='Тест')
        admin = ContentAdmin(Content, AdminSite())
        assert admin.get_categories(content) == 'Все'

    def test_get_categories_returns_names_when_set(
        self, yoga_category: Category, oils_category: Category
    ) -> None:
        content = Content.objects.create(title='Тест')
        content.categories.add(yoga_category, oils_category)
        admin = ContentAdmin(Content, AdminSite())
        result = admin.get_categories(content)
        assert 'Йога' in result
        assert 'Эфирные масла' in result


@pytest.mark.django_db
class TestCategoryAdmin:
    def test_category_admin_list_display(self) -> None:
        admin = CategoryAdmin(Category, AdminSite())
        assert 'name' in admin.list_display
        assert 'code' in admin.list_display
