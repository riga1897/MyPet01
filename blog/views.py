from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from blog.forms import ContentForm
from blog.models import Content
from users.models import is_moderator

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpResponse


class HomeView(ListView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/index.html'
    context_object_name = 'videos'

    def get_queryset(self) -> QuerySet[Content]:
        return Content.objects.all()[:6]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = is_moderator(self.request.user)
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context['is_moderator'] = True
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
