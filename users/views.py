from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect

from django.views.generic import ListView

from users.models import (
    MODERATORS_GROUP_NAME,
    can_manage_moderators,
    get_or_create_moderators_group,
)

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


class ModeratorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    request: Any

    def test_func(self) -> bool:
        return can_manage_moderators(self.request.user)


class ModeratorListView(ModeratorRequiredMixin, ListView):  # type: ignore[type-arg]
    model = User
    template_name = 'users/moderator_list.html'
    context_object_name = 'users'

    def get_queryset(self) -> QuerySet[User]:
        return User.objects.prefetch_related('groups').order_by('username')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        moderators_group = get_or_create_moderators_group()
        context['moderator_ids'] = set(
            User.objects.filter(groups=moderators_group).values_list('id', flat=True)
        )
        context['group_name'] = MODERATORS_GROUP_NAME
        context['is_moderator'] = can_manage_moderators(self.request.user)
        return context


@login_required
@user_passes_test(can_manage_moderators)
def add_moderator(request: HttpRequest, user_id: int) -> HttpResponse:
    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id)
        group = get_or_create_moderators_group()
        user.groups.add(group)
        messages.success(request, f'Пользователь {user.username} добавлен в модераторы.')
    return redirect('users:moderator_list')


@login_required
@user_passes_test(can_manage_moderators)
def remove_moderator(request: HttpRequest, user_id: int) -> HttpResponse:
    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id)
        group = get_or_create_moderators_group()
        user.groups.remove(group)
        messages.success(request, f'Пользователь {user.username} удалён из модераторов.')
    return redirect('users:moderator_list')
