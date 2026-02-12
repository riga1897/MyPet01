from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import shutil
import tempfile
from typing import Any

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from blog.models import Content, ContentType
from blog.views.mixins import ModeratorContextMixin
from core.mixins import ModeratorRequiredMixin
from core.utils.path import safe_media_path


class FileListView(ModeratorRequiredMixin, ModeratorContextMixin, ListView):  # type: ignore[type-arg]
    template_name = 'blog/file_list.html'
    context_object_name = 'content_types'

    def get_queryset(self) -> Any:
        return ContentType.objects.all().order_by('name')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        
        file_to_content: dict[str, dict[str, Any]] = {}
        for content in Content.objects.exclude(video_file='').select_related():
            file_to_content[str(content.video_file)] = {
                'id': content.pk,
                'title': content.title,
            }
        
        all_files: list[dict[str, Any]] = []
        for ct in context['content_types']:
            folder_path = safe_media_path(ct.upload_folder)
            if folder_path and os.path.exists(folder_path) and os.path.isdir(folder_path):
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        relative_path = f'{ct.upload_folder}/{filename}'
                        content_info = file_to_content.get(relative_path)
                        all_files.append({
                            'name': filename,
                            'path': relative_path,
                            'used': content_info is not None,
                            'content_id': content_info['id'] if content_info else None,
                            'content_title': content_info['title'] if content_info else None,
                            'size': os.path.getsize(file_path),
                            'type_id': ct.id,
                            'type_name': ct.name,
                        })
        
        all_files.sort(key=lambda x: str(x['name']).lower())
        context['all_files'] = all_files
        return context


class FileUploadView(ModeratorRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        content_type_id = request.POST.get('content_type_id')
        uploaded_file = request.FILES.get('file')
        
        if not content_type_id or not uploaded_file:
            return JsonResponse({'success': False, 'error': 'Не указан тип или файл'}, status=400)
        
        try:
            ct = ContentType.objects.get(pk=content_type_id)
        except ContentType.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Тип не найден'}, status=404)
        
        folder_path = safe_media_path(ct.upload_folder)
        if folder_path is None:
            return JsonResponse({'success': False, 'error': 'Недопустимая папка'}, status=400)
        
        os.makedirs(folder_path, exist_ok=True)
        
        original_filename = uploaded_file.name or ''
        if '..' in original_filename or '/' in original_filename or '\\' in original_filename:  # pragma: no cover
            return JsonResponse({'success': False, 'error': 'Недопустимое имя файла'}, status=400)
        
        if not original_filename:  # pragma: no cover
            return JsonResponse({'success': False, 'error': 'Пустое имя файла'}, status=400)
        
        md5_hash = hashlib.md5()
        temp_fd, temp_path = tempfile.mkstemp(dir=folder_path)
        try:
            with os.fdopen(temp_fd, 'wb') as temp_file:
                for chunk in uploaded_file.chunks():
                    md5_hash.update(chunk)
                    temp_file.write(chunk)
            
            content_hash = md5_hash.hexdigest()[:8]
            name_part, ext = os.path.splitext(original_filename)
            hashed_filename = f'{name_part}_{content_hash}{ext}'
            file_path = os.path.join(folder_path, hashed_filename)
            
            if os.path.exists(file_path):
                os.remove(temp_path)
                return JsonResponse({
                    'success': True,
                    'filename': hashed_filename,
                    'existing': True,
                    'message': 'Файл уже существует'
                })
            
            shutil.move(temp_path, file_path)
            return JsonResponse({'success': True, 'filename': hashed_filename})
        except Exception:  # pragma: no cover
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise


class FileDeleteView(ModeratorRequiredMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Неверный формат'}, status=400)
        
        file_path_relative = data.get('file_path', '')
        
        if not file_path_relative or '..' in file_path_relative or file_path_relative.startswith('/'):
            return JsonResponse({'success': False, 'error': 'Недопустимый путь'}, status=400)
        
        if Content.objects.filter(video_file=file_path_relative).exists():
            return JsonResponse({'success': False, 'error': 'Файл используется контентом'}, status=400)
        
        full_path = safe_media_path(file_path_relative)
        if full_path is None:  # pragma: no cover
            return JsonResponse({'success': False, 'error': 'Недопустимый путь'}, status=400)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return JsonResponse({'success': False, 'error': 'Файл не найден'}, status=404)
        
        os.remove(full_path)
        return JsonResponse({'success': True})


@method_decorator(login_required, name='dispatch')
class ProtectedMediaView(View):
    """Serve media files only to authenticated users.

    Files are served directly via FileResponse.
    Django handles authentication, then streams the file.
    """

    def get(self, request: HttpRequest, path: str) -> FileResponse:
        full_path = safe_media_path(path)
        if full_path is None:
            raise Http404("Invalid path")

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise Http404("File not found")

        content_type, _ = mimetypes.guess_type(full_path)

        return FileResponse(
            open(full_path, 'rb'),
            content_type=content_type or 'application/octet-stream',
        )
