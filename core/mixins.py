"""Reusable mixins for views."""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from users.models import can_manage_moderators, is_moderator


class ModeratorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки прав модератора."""

    request: Any

    def test_func(self) -> bool:
        """Проверяет, является ли пользователь модератором."""
        return is_moderator(self.request.user)


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки прав администратора."""

    request: Any

    def test_func(self) -> bool:
        """Проверяет, может ли пользователь управлять модераторами."""
        return can_manage_moderators(self.request.user)
