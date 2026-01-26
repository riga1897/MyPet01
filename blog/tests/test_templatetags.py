"""Tests for blog templatetags."""
from blog.templatetags.blog_filters import get_item


class TestGetItemFilter:
    """Tests for get_item template filter."""

    def test_get_item_returns_value_for_existing_key(self) -> None:
        """Test that get_item returns value for existing key."""
        d = {'a': 1, 'b': 2}
        assert get_item(d, 'a') == 1
        assert get_item(d, 'b') == 2

    def test_get_item_returns_none_for_missing_key(self) -> None:
        """Test that get_item returns None for missing key."""
        d = {'a': 1}
        assert get_item(d, 'missing') is None

    def test_get_item_works_with_int_keys(self) -> None:
        """Test that get_item works with integer keys."""
        d = {1: 'one', 2: 'two'}
        assert get_item(d, 1) == 'one'
