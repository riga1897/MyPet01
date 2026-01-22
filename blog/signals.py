"""Signals for cache invalidation."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from blog.cache import invalidate_content_cache
from blog.models import Content, Tag, TagGroup

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


@receiver(m2m_changed, sender=Content.tags.through)
def invalidate_cache_on_tags_changed(
    sender: type[Content],
    instance: Content,
    **kwargs: Any,
) -> None:
    """Invalidate content cache when tags are added/removed."""
    invalidate_content_cache()


@receiver(post_save, sender=Tag)
@receiver(post_delete, sender=Tag)
def invalidate_cache_on_tag_change(
    sender: type[Tag],
    instance: Tag,
    **kwargs: Any,
) -> None:
    """Invalidate content cache when tag is saved or deleted."""
    invalidate_content_cache()


@receiver(post_save, sender=TagGroup)
@receiver(post_delete, sender=TagGroup)
def invalidate_cache_on_taggroup_change(
    sender: type[TagGroup],
    instance: TagGroup,
    **kwargs: Any,
) -> None:
    """Invalidate content cache when tag group is saved or deleted."""
    invalidate_content_cache()
