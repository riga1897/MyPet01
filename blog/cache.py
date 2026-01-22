"""Cache utilities for blog app."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from django.core.cache import cache

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from blog.models import Content

CONTENT_LIST_CACHE_KEY = 'content_list_home'


def get_cached_content_list(limit: int = 6) -> list[Content] | None:
    """Get cached content list or None if not cached."""
    result: Any = cache.get(CONTENT_LIST_CACHE_KEY)
    if result is None:
        return None
    return cast('list[Content]', result)


def set_cached_content_list(queryset: QuerySet[Content], limit: int = 6) -> list[Content]:
    """Cache content list and return it."""
    content_list = list(queryset[:limit])
    cache.set(CONTENT_LIST_CACHE_KEY, content_list)
    return content_list


def invalidate_content_cache() -> None:
    """Clear content list cache."""
    cache.delete(CONTENT_LIST_CACHE_KEY)
