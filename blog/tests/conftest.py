import pytest
from blog.models import Category


@pytest.fixture
def yoga_category() -> Category:
    """Create and return the yoga category."""
    category, _ = Category.objects.get_or_create(
        code='yoga',
        defaults={'name': 'Йога', 'slug': 'yoga'},
    )
    return category


@pytest.fixture
def oils_category() -> Category:
    """Create and return the oils category."""
    category, _ = Category.objects.get_or_create(
        code='oils',
        defaults={'name': 'Эфирные масла', 'slug': 'oils'},
    )
    return category
