from __future__ import annotations

import contextlib
import os
from typing import Any

from django.db import models
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import View

from blog.models import Category, Content, ContentType
from core.utils.path import safe_media_path


class CheckUniqueFieldView(View):
    """Generic API endpoint to check if a model field value is available."""

    model: type[models.Model]
    field_name: str = 'code'
    param_name: str = 'code'

    def get(self, request: HttpRequest) -> HttpResponse:
        value = request.GET.get(self.param_name, '').strip()
        exclude_id_str = request.GET.get('exclude_id')
        exclude_id: int | None = None

        if exclude_id_str:
            with contextlib.suppress(ValueError, TypeError):
                exclude_id = int(exclude_id_str)

        if not value:
            return JsonResponse({'available': True})

        queryset = self.model._default_manager.filter(**{self.field_name: value})
        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)

        available = not queryset.exists()
        return JsonResponse({'available': available, self.param_name: value})


class CheckContentTypeCodeView(CheckUniqueFieldView):
    """Check if ContentType code is available."""
    model = ContentType
    field_name = 'code'
    param_name = 'code'


class CheckContentTypeFolderView(CheckUniqueFieldView):
    """Check if ContentType upload_folder is available."""
    model = ContentType
    field_name = 'upload_folder'
    param_name = 'folder'


class CheckCategoryCodeView(CheckUniqueFieldView):
    """Check if Category code is available."""
    model = Category
    field_name = 'code'
    param_name = 'code'


class BaseAvailableView(View):
    """Base class for listing available files with used-file filtering."""

    folder_source: str = ''
    used_field: str = ''

    def get_folder(self, request: HttpRequest) -> str:
        raise NotImplementedError

    def get_used_files_queryset(self) -> Any:
        return Content.objects.exclude(**{self.used_field: ''})

    def get(self, request: HttpRequest) -> HttpResponse:
        content_id_str = request.GET.get('content_id', '')
        content_id: int | None = None

        if content_id_str:
            with contextlib.suppress(ValueError, TypeError):
                content_id = int(content_id_str)

        folder = self.get_folder(request)
        if not folder:
            return JsonResponse({'files': []})

        folder_path = safe_media_path(folder)
        if folder_path is None:
            return JsonResponse({'files': []})

        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return JsonResponse({'files': []})

        used_files_qs = self.get_used_files_queryset()
        if content_id:
            used_files_qs = used_files_qs.exclude(pk=content_id)
        used_files = set(used_files_qs.values_list(self.used_field, flat=True))

        available_files = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                relative_path = f'{folder}/{filename}'
                if relative_path not in used_files:
                    available_files.append({
                        'name': filename,
                        'path': relative_path,
                    })

        available_files.sort(key=lambda x: x['name'].lower())
        return JsonResponse({'files': available_files})


class AvailableFilesView(BaseAvailableView):
    """API endpoint to get available files for a content type folder."""

    used_field = 'video_file'

    def get_folder(self, request: HttpRequest) -> str:
        return request.GET.get('folder', '').strip()


class AvailableThumbnailsView(BaseAvailableView):
    """API endpoint to get available thumbnail files."""

    used_field = 'thumbnail'

    def get_folder(self, request: HttpRequest) -> str:
        return 'thumbnails'
