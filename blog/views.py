from __future__ import annotations

import json
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from blog.cache import get_cached_content_list, set_cached_content_list
from blog.forms import ContentForm, TagForm, TagGroupForm
from blog.models import Category, Content, ContentType, Tag, TagGroup
from users.models import is_moderator


def get_filter_context() -> dict[str, Any]:
    """Get common filter context (categories, tag groups, and content types)."""
    return {
        'tag_groups': TagGroup.objects.prefetch_related('tags', 'categories').all(),
        'categories': Category.objects.all(),
        'content_types': ContentType.objects.all(),
    }


class HomeView(ListView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/index.html'
    context_object_name = 'videos'

    def get_queryset(self) -> list[Content]:  # type: ignore[override]
        cached = get_cached_content_list()
        if cached is not None:
            return cached
        queryset = Content.objects.select_related('category').prefetch_related(
            'tags', 'tags__group', 'content_types'
        ).all()
        return set_cached_content_list(queryset, limit=6)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = is_moderator(self.request.user)
        context.update(get_filter_context())
        return context


class ModeratorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    request: Any

    def test_func(self) -> bool:
        return is_moderator(self.request.user)


class ContentListView(ModeratorRequiredMixin, ListView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/content_list.html'
    context_object_name = 'contents'
    ordering = ['-created_at']

    def get_queryset(self) -> Any:
        return Content.objects.select_related('category').prefetch_related(
            'tags', 'tags__group'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context.update(get_filter_context())
        return context


class ContentCreateView(ModeratorRequiredMixin, CreateView):  # type: ignore[type-arg]
    model = Content
    form_class = ContentForm
    template_name = 'blog/content_form.html'
    success_url = reverse_lazy('blog:content_list')

    def form_valid(self, form: ContentForm) -> HttpResponse:
        messages.success(self.request, 'Контент успешно создан.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context['action'] = 'Создать'
        context.update(get_filter_context())
        context['selected_tag_ids'] = []
        context['selected_category_id'] = None
        context['selected_content_type_ids'] = []
        context['current_category_code'] = None
        context['has_file'] = False
        return context


class ContentUpdateView(ModeratorRequiredMixin, UpdateView):  # type: ignore[type-arg]
    model = Content
    form_class = ContentForm
    template_name = 'blog/content_form.html'
    success_url = reverse_lazy('blog:content_list')

    def form_valid(self, form: ContentForm) -> HttpResponse:
        messages.success(self.request, 'Контент успешно обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context['action'] = 'Редактировать'
        context.update(get_filter_context())
        content = self.object
        context['selected_tag_ids'] = list(content.tags.values_list('id', flat=True))
        context['selected_category_id'] = content.category_id
        context['selected_content_type_ids'] = list(content.content_types.values_list('id', flat=True))
        context['current_category_code'] = content.category.code if content.category else None
        context['has_file'] = bool(content.video_file)
        return context


class ContentDeleteView(ModeratorRequiredMixin, DeleteView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/content_confirm_delete.html'
    success_url = reverse_lazy('blog:content_list')

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, 'Контент успешно удалён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        return context


class TagListView(ModeratorRequiredMixin, ListView):  # type: ignore[type-arg]
    model = TagGroup
    template_name = 'blog/tag_list.html'
    context_object_name = 'tag_groups'

    def get_queryset(self) -> Any:
        return TagGroup.objects.prefetch_related('tags', 'categories').all()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context.update(get_filter_context())
        return context


class TagGroupCreateView(ModeratorRequiredMixin, CreateView):  # type: ignore[type-arg]
    model = TagGroup
    form_class = TagGroupForm
    template_name = 'blog/taggroup_form.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: TagGroupForm) -> HttpResponse:
        messages.success(self.request, 'Группа тегов успешно создана.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context['action'] = 'Создать группу'
        return context


class TagGroupUpdateView(ModeratorRequiredMixin, UpdateView):  # type: ignore[type-arg]
    model = TagGroup
    form_class = TagGroupForm
    template_name = 'blog/taggroup_form.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: TagGroupForm) -> HttpResponse:
        messages.success(self.request, 'Группа тегов успешно обновлена.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context['action'] = 'Редактировать группу'
        return context


class TagGroupDeleteView(ModeratorRequiredMixin, DeleteView):  # type: ignore[type-arg]
    model = TagGroup
    template_name = 'blog/taggroup_confirm_delete.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, 'Группа тегов успешно удалена.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        return context


class TagCreateView(ModeratorRequiredMixin, CreateView):  # type: ignore[type-arg]
    model = Tag
    form_class = TagForm
    template_name = 'blog/tag_form.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: TagForm) -> HttpResponse:
        messages.success(self.request, 'Тег успешно создан.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context['action'] = 'Создать тег'
        return context


class TagUpdateView(ModeratorRequiredMixin, UpdateView):  # type: ignore[type-arg]
    model = Tag
    form_class = TagForm
    template_name = 'blog/tag_form.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: TagForm) -> HttpResponse:
        messages.success(self.request, 'Тег успешно обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context['action'] = 'Редактировать тег'
        return context


class TagDeleteView(ModeratorRequiredMixin, DeleteView):  # type: ignore[type-arg]
    model = Tag
    template_name = 'blog/tag_confirm_delete.html'
    success_url = reverse_lazy('blog:tag_list')

    def form_valid(self, form: Any) -> HttpResponse:
        messages.success(self.request, 'Тег успешно удалён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        return context


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
        
        if not queryset.exists():
            return JsonResponse({'available': True, 'code': code})
        
        from blog.models import generate_unique_code
        suggested = generate_unique_code(ContentType, code, exclude_id)
        
        return JsonResponse({
            'available': False,
            'code': code,
            'suggested': suggested,
        })
