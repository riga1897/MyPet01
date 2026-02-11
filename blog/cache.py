"""Cache utilities for blog app."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from django.core.cache import cache

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from blog.models import Category, Content, ContentType, TagGroup

CONTENT_LIST_CACHE_KEY = 'content_list_home_ids'
FILTER_CONTEXT_CACHE_KEY = 'filter_context'
CACHE_TTL = 300  # 5 minutes


def get_cached_content_ids() -> list[int] | None:
    """Get cached content IDs or None if not cached."""
    result: Any = cache.get(CONTENT_LIST_CACHE_KEY)
    if result is None:
        return None
    return cast(list[int], result)


def set_cached_content_ids(queryset: QuerySet[Content], limit: int = 6) -> list[int]:
    """Cache content IDs and return them."""
    content_ids = list(queryset.values_list('id', flat=True)[:limit])
    cache.set(CONTENT_LIST_CACHE_KEY, content_ids, timeout=CACHE_TTL)
    return content_ids


def invalidate_content_cache() -> None:
    """Clear content list cache."""
    cache.delete(CONTENT_LIST_CACHE_KEY)


def get_cached_filter_context() -> dict[str, Any] | None:
    """Get cached filter context or None if not cached."""
    result: Any = cache.get(FILTER_CONTEXT_CACHE_KEY)
    if result is None:
        return None
    return cast(dict[str, Any], result)


def set_cached_filter_context(
    tag_groups: QuerySet[TagGroup],
    categories: QuerySet[Category],
    content_types: QuerySet[ContentType],
) -> dict[str, Any]:
    """Cache filter context and return it."""
    context: dict[str, Any] = {
        'tag_groups': list(tag_groups),
        'categories': list(categories),
        'content_types': list(content_types),
    }
    cache.set(FILTER_CONTEXT_CACHE_KEY, context, timeout=CACHE_TTL)
    return context


def invalidate_filter_context_cache() -> None:
    """Clear filter context cache."""
    cache.delete(FILTER_CONTEXT_CACHE_KEY)
