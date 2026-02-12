from __future__ import annotations

import os
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from blog.cache import (
    get_cached_filter_context,
    set_cached_filter_context,
)
from blog.forms import ContentForm
from blog.models import Category, ContentType, TagGroup
from core.utils.path import safe_media_path


def get_filter_context() -> dict[str, Any]:
    """Get common filter context (categories, tag groups, and content types).
    
    Uses caching to avoid repeated database queries.
    """
    cached = get_cached_filter_context()
    if cached is not None:
        return cached
    
    tag_groups = TagGroup.objects.prefetch_related('tags', 'categories').all()
    categories = Category.objects.all()
    content_types = ContentType.objects.all()
    
    return set_cached_filter_context(tag_groups, categories, content_types)


def get_available_thumbnails() -> list[str]:
    """Get list of available thumbnail files."""
    thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
    if not os.path.exists(thumbnails_path) or not os.path.isdir(thumbnails_path):
        return []
    
    thumbnails = []
    for filename in os.listdir(thumbnails_path):
        file_path = os.path.join(thumbnails_path, filename)
        if os.path.isfile(file_path):
            thumbnails.append(f'thumbnails/{filename}')
    
    return sorted(thumbnails, key=str.lower)


def validate_media_path(path: str, expected_prefix: str) -> bool:
    """Validate that a media path is safe and exists under expected prefix.

    Checks for path traversal, prefix match, and file existence.
    """
    if not path:
        return False
    if '..' in path or path.startswith('/'):
        return False
    if not path.startswith(expected_prefix):
        return False
    full_path = safe_media_path(path)
    if full_path is None:  # pragma: no cover
        return False
    return os.path.exists(full_path) and os.path.isfile(full_path)


def validate_existing_file(existing_file: str, content_type: ContentType | None) -> bool:
    """Validate that existing_file is safe and exists in content_type folder."""
    if not content_type:
        return False
    return validate_media_path(existing_file, content_type.upload_folder + '/')


def validate_existing_thumbnail(existing_thumbnail: str) -> bool:
    """Validate that existing_thumbnail is safe and exists in thumbnails folder."""
    return validate_media_path(existing_thumbnail, 'thumbnails/')


class ModeratorContextMixin:
    """Mixin that adds is_moderator=True to context."""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)  # type: ignore[misc]
        context['is_moderator'] = True
        return context


class ModeratorFilterContextMixin(ModeratorContextMixin):
    """Mixin that adds is_moderator=True and filter context to views."""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context.update(get_filter_context())
        return context


class FileHandlingMixin:
    """Mixin for handling existing_file and existing_thumbnail in content forms."""

    request: HttpRequest

    def handle_file_selection(
        self, form: ContentForm, allow_detach: bool = False
    ) -> HttpResponse | None:
        """Handle file and thumbnail selection from existing files.
        
        Returns HttpResponse (form_invalid) on error, None on success.
        """
        if allow_detach:
            detach_file = self.request.POST.get('detach_file', '').strip()
            if detach_file == 'true':
                form.instance.video_file = ''
            else:
                error = self._handle_existing_file(form)
                if error:
                    return error
            
            detach_thumbnail = self.request.POST.get('detach_thumbnail', '').strip()
            if detach_thumbnail == 'true':
                form.instance.thumbnail = ''
            else:
                error = self._handle_existing_thumbnail(form)
                if error:
                    return error
        else:
            error = self._handle_existing_file(form)
            if error:
                return error
            error = self._handle_existing_thumbnail(form)
            if error:
                return error
        
        return None

    def _handle_existing_file(self, form: ContentForm) -> HttpResponse | None:
        """Handle existing_file field."""
        existing_file = self.request.POST.get('existing_file', '').strip()
        if existing_file:
            if validate_existing_file(existing_file, form.instance.content_type):
                form.instance.video_file = existing_file
            else:
                form.add_error(None, 'Выбранный файл недоступен.')
                result: HttpResponse = self.form_invalid(form)  # type: ignore[attr-defined]
                return result
        return None

    def _handle_existing_thumbnail(self, form: ContentForm) -> HttpResponse | None:
        """Handle existing_thumbnail field."""
        existing_thumbnail = self.request.POST.get('existing_thumbnail', '').strip()
        if existing_thumbnail:
            if validate_existing_thumbnail(existing_thumbnail):
                form.instance.thumbnail = existing_thumbnail
            else:
                form.add_error(None, 'Выбранная миниатюра недоступна.')
                result: HttpResponse = self.form_invalid(form)  # type: ignore[attr-defined]
                return result
        return None
