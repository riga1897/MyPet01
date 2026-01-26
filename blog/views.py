from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from typing import Any

from django.conf import settings
from django.contrib import messages
from core.mixins import ModeratorRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from blog.cache import (
    get_cached_content_ids,
    get_cached_filter_context,
    set_cached_content_ids,
    set_cached_filter_context,
)
from blog.forms import ContentForm, TagForm, TagGroupForm
from blog.models import Category, Content, ContentType, Tag, TagGroup
from users.models import is_moderator


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


class HomeView(ListView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/index.html'
    context_object_name = 'videos'

    def get_queryset(self) -> list[Content]:  # type: ignore[override]
        """Get content list, using cached IDs for efficiency."""
        cached_ids = get_cached_content_ids()
        if cached_ids is not None:
            return list(
                Content.objects.select_related('content_type')
                .prefetch_related('categories', 'tags', 'tags__group')
                .filter(id__in=cached_ids)
            )
        
        queryset = Content.objects.select_related('content_type').prefetch_related(
            'categories', 'tags', 'tags__group'
        ).all()
        set_cached_content_ids(queryset, limit=6)
        return list(queryset[:6])

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = is_moderator(self.request.user)
        context.update(get_filter_context())
        return context


class ContentListView(ModeratorRequiredMixin, ModeratorFilterContextMixin, ListView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/content_list.html'
    context_object_name = 'contents'
    ordering = ['-created_at']

    def get_queryset(self) -> Any:
        return Content.objects.select_related('content_type').prefetch_related(
            'categories', 'tags', 'tags__group'
        ).order_by('-created_at')


def validate_existing_file(existing_file: str, content_type: ContentType | None) -> bool:
    """Validate that existing_file is safe and exists in content_type folder."""
    if not existing_file or not content_type:
        return False
    if '..' in existing_file or existing_file.startswith('/'):
        return False
    expected_prefix = content_type.upload_folder + '/'
    if not existing_file.startswith(expected_prefix):
        return False
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, existing_file))
    media_root = os.path.normpath(settings.MEDIA_ROOT)
    if not full_path.startswith(media_root + os.sep):
        return False
    return os.path.exists(full_path) and os.path.isfile(full_path)


def validate_existing_thumbnail(existing_thumbnail: str) -> bool:
    """Validate that existing_thumbnail is safe and exists in thumbnails folder."""
    if not existing_thumbnail:
        return False
    if '..' in existing_thumbnail or existing_thumbnail.startswith('/'):
        return False
    if not existing_thumbnail.startswith('thumbnails/'):
        return False
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, existing_thumbnail))
    media_root = os.path.normpath(settings.MEDIA_ROOT)
    if not full_path.startswith(media_root + os.sep):
        return False
    return os.path.exists(full_path) and os.path.isfile(full_path)


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


class ContentCreateView(ModeratorRequiredMixin, ModeratorFilterContextMixin, FileHandlingMixin, CreateView):  # type: ignore[type-arg]
    model = Content
    form_class = ContentForm
    template_name = 'blog/content_form.html'
    success_url = reverse_lazy('blog:content_list')

    def form_valid(self, form: ContentForm) -> HttpResponse:
        error = self.handle_file_selection(form, allow_detach=False)
        if error:
            return error
        
        messages.success(self.request, 'Контент успешно создан.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['action'] = 'Создать'
        context['selected_tag_ids'] = []
        context['selected_category_ids'] = []
        context['selected_category_codes'] = []
        context['selected_content_type_id'] = None
        context['has_file'] = False
        context['available_thumbnails'] = get_available_thumbnails()
        return context


class ContentUpdateView(ModeratorRequiredMixin, ModeratorFilterContextMixin, FileHandlingMixin, UpdateView):  # type: ignore[type-arg]
    model = Content
    form_class = ContentForm
    template_name = 'blog/content_form.html'
    success_url = reverse_lazy('blog:content_list')

    def form_valid(self, form: ContentForm) -> HttpResponse:
        error = self.handle_file_selection(form, allow_detach=True)
        if error:
            return error
        
        messages.success(self.request, 'Контент успешно обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['action'] = 'Редактировать'
        content = self.object
        context['selected_tag_ids'] = list(content.tags.values_list('id', flat=True))
        context['selected_category_ids'] = list(content.categories.values_list('id', flat=True))
        context['selected_category_codes'] = list(content.categories.values_list('code', flat=True))
        context['selected_content_type_id'] = content.content_type_id
        context['has_file'] = bool(content.video_file)
        context['available_thumbnails'] = get_available_thumbnails()
        return context


class ContentDeleteView(ModeratorRequiredMixin, ModeratorContextMixin, DeleteView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/content_confirm_delete.html'
    success_url = reverse_lazy('blog:content_list')

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, 'Контент успешно удалён.')
        return super().form_valid(form)


class TagListView(ModeratorRequiredMixin, ModeratorFilterContextMixin, ListView):  # type: ignore[type-arg]
    model = TagGroup
    template_name = 'blog/tag_list.html'
    context_object_name = 'tag_groups'

    def get_queryset(self) -> Any:
        return TagGroup.objects.prefetch_related('tags', 'categories').all()


class TagGroupCreateView(ModeratorRequiredMixin, ModeratorContextMixin, CreateView):  # type: ignore[type-arg]
    model = TagGroup
    form_class = TagGroupForm
    template_name = 'blog/taggroup_form.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: TagGroupForm) -> HttpResponse:
        messages.success(self.request, 'Группа тегов успешно создана.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['action'] = 'Создать группу'
        return context


class TagGroupUpdateView(ModeratorRequiredMixin, ModeratorContextMixin, UpdateView):  # type: ignore[type-arg]
    model = TagGroup
    form_class = TagGroupForm
    template_name = 'blog/taggroup_form.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: TagGroupForm) -> HttpResponse:
        messages.success(self.request, 'Группа тегов успешно обновлена.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['action'] = 'Редактировать группу'
        return context


class TagGroupDeleteView(ModeratorRequiredMixin, ModeratorContextMixin, DeleteView):  # type: ignore[type-arg]
    model = TagGroup
    template_name = 'blog/taggroup_confirm_delete.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, 'Группа тегов успешно удалена.')
        return super().form_valid(form)


class TagCreateView(ModeratorRequiredMixin, ModeratorContextMixin, CreateView):  # type: ignore[type-arg]
    model = Tag
    form_class = TagForm
    template_name = 'blog/tag_form.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: TagForm) -> HttpResponse:
        messages.success(self.request, 'Тег успешно создан.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['action'] = 'Создать тег'
        return context


class TagUpdateView(ModeratorRequiredMixin, ModeratorContextMixin, UpdateView):  # type: ignore[type-arg]
    model = Tag
    form_class = TagForm
    template_name = 'blog/tag_form.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: TagForm) -> HttpResponse:
        messages.success(self.request, 'Тег успешно обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['action'] = 'Редактировать тег'
        return context


class TagDeleteView(ModeratorRequiredMixin, ModeratorContextMixin, DeleteView):  # type: ignore[type-arg]
    model = Tag
    template_name = 'blog/tag_confirm_delete.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, 'Тег успешно удалён.')
        return super().form_valid(form)


class TagReorderView(ModeratorRequiredMixin, View):
    """AJAX endpoint for reordering tags via drag-and-drop."""

    def post(self, request: Any, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            data = json.loads(request.body)
            tag_ids = data.get('tag_ids', [])
            group_id = data.get('group_id')

            if not tag_ids:
                return JsonResponse({'error': 'No tag IDs provided'}, status=400)

            if not group_id:
                return JsonResponse({'error': 'No group ID provided'}, status=400)

            tags = list(Tag.objects.filter(pk__in=tag_ids))
            if len(tags) != len(tag_ids):
                return JsonResponse({'error': 'Some tags not found'}, status=400)

            for tag in tags:
                if tag.group.pk != int(group_id):
                    return JsonResponse(
                        {'error': 'All tags must belong to the same group'},
                        status=400,
                    )

            tag_id_to_order = {tag_id: order for order, tag_id in enumerate(tag_ids)}
            for tag in tags:
                tag.order = tag_id_to_order[tag.pk]
                tag.save(update_fields=['order'])

            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class CheckContentTypeCodeView(View):
    """API endpoint to check if ContentType code is available."""

    def get(self, request: HttpRequest) -> HttpResponse:
        code = request.GET.get('code', '').strip()
        exclude_id_str = request.GET.get('exclude_id')
        exclude_id: int | None = None
        
        if exclude_id_str:
            try:
                exclude_id = int(exclude_id_str)
            except (ValueError, TypeError):
                pass
        
        if not code:
            return JsonResponse({'available': True})
        
        queryset = ContentType.objects.filter(code=code)
        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)
        
        available = not queryset.exists()
        return JsonResponse({'available': available, 'code': code})


class CheckContentTypeFolderView(View):
    """API endpoint to check if ContentType upload_folder is available."""

    def get(self, request: HttpRequest) -> HttpResponse:
        folder = request.GET.get('folder', '').strip()
        exclude_id_str = request.GET.get('exclude_id')
        exclude_id: int | None = None
        
        if exclude_id_str:
            try:
                exclude_id = int(exclude_id_str)
            except (ValueError, TypeError):
                pass
        
        if not folder:
            return JsonResponse({'available': True})
        
        queryset = ContentType.objects.filter(upload_folder=folder)
        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)
        
        available = not queryset.exists()
        return JsonResponse({'available': available, 'folder': folder})


class CheckCategoryCodeView(View):
    """API endpoint to check if Category code is available."""

    def get(self, request: HttpRequest) -> HttpResponse:
        code = request.GET.get('code', '').strip()
        exclude_id_str = request.GET.get('exclude_id')
        exclude_id: int | None = None
        
        if exclude_id_str:
            try:
                exclude_id = int(exclude_id_str)
            except (ValueError, TypeError):
                pass
        
        if not code:
            return JsonResponse({'available': True})
        
        queryset = Category.objects.filter(code=code)
        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)
        
        available = not queryset.exists()
        return JsonResponse({'available': available, 'code': code})


class AvailableFilesView(View):
    """API endpoint to get available files for a content type folder."""

    def get(self, request: HttpRequest) -> HttpResponse:
        folder = request.GET.get('folder', '').strip()
        content_id_str = request.GET.get('content_id', '')
        content_id: int | None = None
        
        if content_id_str:
            try:
                content_id = int(content_id_str)
            except (ValueError, TypeError):
                pass
        
        if not folder or '..' in folder or folder.startswith('/'):
            return JsonResponse({'files': []})
        
        folder_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, folder))
        media_root = os.path.normpath(settings.MEDIA_ROOT)
        if not folder_path.startswith(media_root + os.sep):
            return JsonResponse({'files': []})
        
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return JsonResponse({'files': []})
        
        used_files_qs = Content.objects.exclude(video_file='')
        if content_id:
            used_files_qs = used_files_qs.exclude(pk=content_id)
        used_files = set(used_files_qs.values_list('video_file', flat=True))
        
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


class AvailableThumbnailsView(View):
    """API endpoint to get available thumbnail files."""

    def get(self, request: HttpRequest) -> HttpResponse:
        content_id_str = request.GET.get('content_id', '')
        content_id: int | None = None
        
        if content_id_str:
            try:
                content_id = int(content_id_str)
            except (ValueError, TypeError):
                pass
        
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        if not os.path.exists(thumbnails_path) or not os.path.isdir(thumbnails_path):
            return JsonResponse({'files': []})
        
        used_thumbs_qs = Content.objects.exclude(thumbnail='')
        if content_id:
            used_thumbs_qs = used_thumbs_qs.exclude(pk=content_id)
        used_thumbs = set(used_thumbs_qs.values_list('thumbnail', flat=True))
        
        available_files = []
        for filename in os.listdir(thumbnails_path):
            file_path = os.path.join(thumbnails_path, filename)
            if os.path.isfile(file_path):
                relative_path = f'thumbnails/{filename}'
                if relative_path not in used_thumbs:
                    available_files.append({
                        'name': filename,
                        'path': relative_path,
                    })
        
        available_files.sort(key=lambda x: x['name'].lower())
        return JsonResponse({'files': available_files})


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
            folder_path = os.path.join(settings.MEDIA_ROOT, ct.upload_folder)
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
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
        
        folder_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, ct.upload_folder))
        media_root = os.path.normpath(settings.MEDIA_ROOT)
        if not folder_path.startswith(media_root + os.sep):
            return JsonResponse({'success': False, 'error': 'Недопустимая папка'}, status=400)
        
        os.makedirs(folder_path, exist_ok=True)
        
        original_filename = uploaded_file.name or ''
        if '..' in original_filename or '/' in original_filename or '\\' in original_filename:
            return JsonResponse({'success': False, 'error': 'Недопустимое имя файла'}, status=400)
        
        if not original_filename:
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
        except Exception:
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
        
        full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, file_path_relative))
        media_root = os.path.normpath(settings.MEDIA_ROOT)
        if not full_path.startswith(media_root + os.sep):
            return JsonResponse({'success': False, 'error': 'Недопустимый путь'}, status=400)
        
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return JsonResponse({'success': False, 'error': 'Файл не найден'}, status=404)
        
        os.remove(full_path)
        return JsonResponse({'success': True})
