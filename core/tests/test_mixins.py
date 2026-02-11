"""Tests for core mixins."""

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.views import View

from core.mixins import AdminRequiredMixin, ModeratorRequiredMixin
from users.models import get_or_create_moderators_group


class DummyModeratorView(ModeratorRequiredMixin, View):
    """Dummy view for testing ModeratorRequiredMixin."""

    def get(self, request):  # type: ignore[no-untyped-def]
        return "OK"


class DummyAdminView(AdminRequiredMixin, View):
    """Dummy view for testing AdminRequiredMixin."""

    def get(self, request):  # type: ignore[no-untyped-def]
        return "OK"


@pytest.fixture
def factory() -> RequestFactory:
    """Create request factory."""
    return RequestFactory()


@pytest.fixture
def regular_user(db: None) -> User:
    """Create a regular user."""
    return User.objects.create_user(username="regular", password="testpass123")


@pytest.fixture
def moderator_user(db: None) -> User:
    """Create a moderator user."""
    user = User.objects.create_user(username="moderator", password="testpass123")
    group = get_or_create_moderators_group()
    user.groups.add(group)
    return user


@pytest.fixture
def admin_user(db: None) -> User:
    """Create an admin (superuser)."""
    return User.objects.create_superuser(
        username="admin", email="admin@test.com", password="testpass123"
    )


class TestModeratorRequiredMixin:
    """Tests for ModeratorRequiredMixin."""

    def test_moderator_passes(
        self, factory: RequestFactory, moderator_user: User
    ) -> None:
        """Moderator user should pass the test."""
        request = factory.get("/")
        request.user = moderator_user
        view = DummyModeratorView()
        view.request = request
        assert view.test_func() is True

    def test_regular_user_fails(
        self, factory: RequestFactory, regular_user: User
    ) -> None:
        """Regular user should fail the test."""
        request = factory.get("/")
        request.user = regular_user
        view = DummyModeratorView()
        view.request = request
        assert view.test_func() is False

    def test_admin_passes(self, factory: RequestFactory, admin_user: User) -> None:
        """Admin user should pass the test (superuser is always moderator)."""
        request = factory.get("/")
        request.user = admin_user
        view = DummyModeratorView()
        view.request = request
        assert view.test_func() is True


class TestAdminRequiredMixin:
    """Tests for AdminRequiredMixin."""

    def test_admin_passes(self, factory: RequestFactory, admin_user: User) -> None:
        """Admin user should pass the test."""
        request = factory.get("/")
        request.user = admin_user
        view = DummyAdminView()
        view.request = request
        assert view.test_func() is True

    def test_moderator_fails(
        self, factory: RequestFactory, moderator_user: User
    ) -> None:
        """Moderator user should fail (only superuser can manage moderators)."""
        request = factory.get("/")
        request.user = moderator_user
        view = DummyAdminView()
        view.request = request
        assert view.test_func() is False

    def test_regular_user_fails(
        self, factory: RequestFactory, regular_user: User
    ) -> None:
        """Regular user should fail the test."""
        request = factory.get("/")
        request.user = regular_user
        view = DummyAdminView()
        view.request = request
        assert view.test_func() is False
