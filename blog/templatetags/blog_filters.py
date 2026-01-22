from typing import Any

from django import template

register = template.Library()


@register.filter
def get_item(dictionary: dict[Any, Any], key: Any) -> Any:
    """Get item from dictionary by key."""
    return dictionary.get(key)
