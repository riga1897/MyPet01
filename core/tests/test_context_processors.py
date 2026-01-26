"""Tests for context processors."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from core.context_processors import user_permissions
from users.models import get_or_create_moderators_group

User = get_user_model()


@pytest.fixture
def factory() -> RequestFactory:
    return RequestFactory()


@pytest.mark.django_db
class TestUserPermissionsContextProcessor:
    def test_anonymous_user_is_not_moderator(self, factory: RequestFactory) -> None:
        """Anonymous user should have is_moderator=False."""
        request = factory.get("/")
        request.user = AnonymousUser()
        context = user_permissions(request)
        assert context["is_moderator"] is False

    def test_regular_user_is_not_moderator(self, factory: RequestFactory) -> None:
        """Regular user should have is_moderator=False."""
        user = User.objects.create_user(username="regular", password="test123")
        request = factory.get("/")
        request.user = user
        context = user_permissions(request)
        assert context["is_moderator"] is False

    def test_moderator_user_is_moderator(self, factory: RequestFactory) -> None:
        """User in moderators group should have is_moderator=True."""
        user = User.objects.create_user(username="mod", password="test123")
        group = get_or_create_moderators_group()
        user.groups.add(group)
        request = factory.get("/")
        request.user = user
        context = user_permissions(request)
        assert context["is_moderator"] is True

    def test_superuser_is_moderator(self, factory: RequestFactory) -> None:
        """Superuser should have is_moderator=True."""
        user = User.objects.create_superuser(username="admin", password="test123")
        request = factory.get("/")
        request.user = user
        context = user_permissions(request)
        assert context["is_moderator"] is True
