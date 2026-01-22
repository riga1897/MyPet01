from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from blog.cache import get_cached_content_list, set_cached_content_list
from blog.forms import ContentForm, TagForm, TagGroupForm
from blog.models import Content, Tag, TagGroup
from users.models import is_moderator

if TYPE_CHECKING:
    from django.http import HttpResponse


class HomeView(ListView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/index.html'
    context_object_name = 'videos'

    def get_queryset(self) -> list[Content]:  # type: ignore[override]
        cached = get_cached_content_list()
        if cached is not None:
            return cached
        queryset = Content.objects.prefetch_related('tags', 'tags__group').all()
        return set_cached_content_list(queryset, limit=6)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = is_moderator(self.request.user)
        context['tag_groups'] = TagGroup.objects.prefetch_related('tags').all()
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
        return Content.objects.prefetch_related('tags', 'tags__group').order_by('-created_at')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
        context['tag_groups'] = TagGroup.objects.prefetch_related('tags').all()
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
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
