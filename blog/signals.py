"""Signals for cache invalidation."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from blog.cache import invalidate_content_cache
from blog.models import Content

if TYPE_CHECKING:
    pass


@receiver(post_save, sender=Content)
def invalidate_cache_on_save(
    sender: type[Content],
    instance: Content,
    **kwargs: Any,
) -> None:
    """Invalidate content cache when content is saved."""
    invalidate_content_cache()


@receiver(post_delete, sender=Content)
def invalidate_cache_on_delete(
    sender: type[Content],
    instance: Content,
    **kwargs: Any,
) -> None:
    """Invalidate content cache when content is deleted."""
    invalidate_content_cache()
