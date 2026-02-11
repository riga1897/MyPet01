"""Tests for blog/utils.py filtering utilities."""
import pytest
from blog.models import Category, Content, Tag, TagGroup
from blog.utils import filter_content, filter_tag_groups, get_visible_tag_groups


@pytest.fixture
def yoga_category(db: None) -> Category:
    cat, _ = Category.objects.get_or_create(code='yoga', defaults={'name': 'Йога'})
    return cat


@pytest.fixture
def oils_category(db: None) -> Category:
    cat, _ = Category.objects.get_or_create(code='oils', defaults={'name': 'Масла'})
    return cat


@pytest.fixture
def yoga_tag_group(yoga_category: Category) -> TagGroup:
    group = TagGroup.objects.create(name='Йога группа')
    group.categories.add(yoga_category)
    return group


@pytest.fixture
def all_category_group(db: None) -> TagGroup:
    return TagGroup.objects.create(name='Все группа')


@pytest.fixture
def yoga_content(yoga_category: Category) -> Content:
    content = Content.objects.create(
        title='Йога контент',
        description='Описание йоги',
    )
    content.categories.add(yoga_category)
    return content


@pytest.fixture
def oils_content(oils_category: Category) -> Content:
    content = Content.objects.create(
        title='Масла контент',
        description='Описание масел',
    )
    content.categories.add(oils_category)
    return content


@pytest.mark.django_db
class TestFilterContent:
    """Tests for filter_content function."""

    def test_filter_by_category(
        self, yoga_content: Content, oils_content: Content, yoga_category: Category
    ) -> None:
        queryset = Content.objects.all()
        result = filter_content(queryset, category=yoga_category)
        assert yoga_content in result
        assert oils_content not in result

    def test_filter_by_search_query(
        self, yoga_content: Content, oils_content: Content
    ) -> None:
        queryset = Content.objects.all()
        result = filter_content(queryset, search_query='йога')
        assert yoga_content in result
        assert oils_content not in result

    def test_filter_by_tags(
        self, yoga_content: Content, oils_content: Content, yoga_tag_group: TagGroup
    ) -> None:
        tag = Tag.objects.create(name='Тест', group=yoga_tag_group)
        yoga_content.tags.add(tag)
        
        queryset = Content.objects.all()
        result = filter_content(queryset, tags=[tag])
        assert yoga_content in result
        assert oils_content not in result

    def test_combined_filters(
        self,
        yoga_content: Content,
        oils_content: Content,
        yoga_category: Category,
        yoga_tag_group: TagGroup,
    ) -> None:
        tag = Tag.objects.create(name='Тег', group=yoga_tag_group)
        yoga_content.tags.add(tag)
        
        queryset = Content.objects.all()
        result = filter_content(
            queryset,
            category=yoga_category,
            tags=[tag],
            search_query='йога',
        )
        assert yoga_content in result
        assert oils_content not in result

    def test_no_filters_returns_all(
        self, yoga_content: Content, oils_content: Content
    ) -> None:
        queryset = Content.objects.all()
        result = filter_content(queryset)
        assert yoga_content in result
        assert oils_content in result

    def test_filter_no_category(
        self, yoga_content: Content, oils_content: Content
    ) -> None:
        no_cat_content = Content.objects.create(
            title='Без категории',
            description='Контент без категории',
        )
        queryset = Content.objects.all()
        result = filter_content(queryset, no_category=True)
        assert no_cat_content in result
        assert yoga_content not in result
        assert oils_content not in result


@pytest.mark.django_db
class TestGetVisibleTagGroups:
    """Tests for get_visible_tag_groups function."""

    def test_empty_categories_visible_for_all(
        self, all_category_group: TagGroup, yoga_category: Category
    ) -> None:
        groups = TagGroup.objects.all()
        result = get_visible_tag_groups(groups, category=yoga_category)
        assert all_category_group in result

    def test_specific_category_visibility(
        self, yoga_tag_group: TagGroup, yoga_category: Category, oils_category: Category
    ) -> None:
        groups = TagGroup.objects.all()
        
        yoga_result = get_visible_tag_groups(groups, category=yoga_category)
        assert yoga_tag_group in yoga_result
        
        oils_result = get_visible_tag_groups(groups, category=oils_category)
        assert yoga_tag_group not in oils_result

    def test_none_category_returns_all(
        self, yoga_tag_group: TagGroup, all_category_group: TagGroup
    ) -> None:
        groups = TagGroup.objects.all()
        result = get_visible_tag_groups(groups, category=None)
        assert yoga_tag_group in result
        assert all_category_group in result


@pytest.mark.django_db
class TestFilterTagGroups:
    """Tests for filter_tag_groups function."""

    def test_filter_by_category(
        self,
        yoga_tag_group: TagGroup,
        all_category_group: TagGroup,
        yoga_category: Category,
        oils_category: Category,
    ) -> None:
        queryset = TagGroup.objects.all()
        
        yoga_result = filter_tag_groups(queryset, category=yoga_category)
        assert yoga_tag_group in yoga_result
        assert all_category_group in yoga_result
        
        oils_result = list(filter_tag_groups(queryset, category=oils_category))
        assert yoga_tag_group not in oils_result
        assert all_category_group in oils_result

    def test_filter_by_search_query(
        self, yoga_tag_group: TagGroup, all_category_group: TagGroup
    ) -> None:
        queryset = TagGroup.objects.all()
        result = filter_tag_groups(queryset, search_query='йога')
        assert yoga_tag_group in result
        assert all_category_group not in result

    def test_search_by_tag_name(self, yoga_tag_group: TagGroup) -> None:
        Tag.objects.create(name='Особый тег', group=yoga_tag_group)
        
        queryset = TagGroup.objects.all()
        result = filter_tag_groups(queryset, search_query='особый')
        assert yoga_tag_group in result

    def test_no_filters_returns_all(
        self, yoga_tag_group: TagGroup, all_category_group: TagGroup
    ) -> None:
        queryset = TagGroup.objects.all()
        result = filter_tag_groups(queryset)
        assert yoga_tag_group in result
        assert all_category_group in result

    def test_filter_no_category(
        self, yoga_tag_group: TagGroup, all_category_group: TagGroup
    ) -> None:
        queryset = TagGroup.objects.all()
        result = filter_tag_groups(queryset, no_category=True)
        assert all_category_group in result
        assert yoga_tag_group not in result
