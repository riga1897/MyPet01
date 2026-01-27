"""Tests for blog admin classes."""
from typing import Any

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.test import RequestFactory

from blog.admin import ContentAdmin, ContentTypeAdmin, TagGroupAdmin
from blog.models import Category, Content, ContentType, TagGroup

User = get_user_model()


def get_request_with_messages(user: Any, factory: RequestFactory) -> HttpRequest:
    """Create a request with session and message support."""
    request = factory.post('/')
    request.user = user
    middleware = SessionMiddleware(lambda r: r)
    middleware.process_request(request)
    request.session.save()
    request._messages = FallbackStorage(request)
    return request


@pytest.fixture
def admin_user() -> Any:
    return User.objects.create_superuser('admin', 'admin@test.com', 'password')


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def site() -> AdminSite:
    return AdminSite()


@pytest.mark.django_db
class TestContentTypeAdmin:
    """Tests for ContentTypeAdmin."""

    def test_content_count_returns_count(self, site: AdminSite) -> None:
        """Test content_count method returns correct count."""
        ct = ContentType.objects.create(name='Тип Счётчик', code='counter', upload_folder='cnt')
        Content.objects.create(title='Тест1', content_type=ct)
        Content.objects.create(title='Тест2', content_type=ct)
        admin = ContentTypeAdmin(ContentType, site)
        assert admin.content_count(ct) == 2

    def test_delete_model_success(
        self, site: AdminSite, admin_user: Any, request_factory: RequestFactory
    ) -> None:
        """Test successful single deletion."""
        ct = ContentType.objects.create(name='Удаляемый', code='del', upload_folder='del')
        admin = ContentTypeAdmin(ContentType, site)
        request = get_request_with_messages(admin_user, request_factory)
        admin.delete_model(request, ct)
        assert not ContentType.objects.filter(code='del').exists()

    def test_delete_model_with_content_shows_error(
        self, site: AdminSite, admin_user: Any, request_factory: RequestFactory
    ) -> None:
        """Test deletion with content shows error message."""
        ct = ContentType.objects.create(name='С контентом', code='has', upload_folder='has')
        Content.objects.create(title='Связанный', content_type=ct)
        admin = ContentTypeAdmin(ContentType, site)
        request = get_request_with_messages(admin_user, request_factory)
        admin.delete_model(request, ct)
        assert ContentType.objects.filter(code='has').exists()

    def test_delete_queryset_partial_success(
        self, site: AdminSite, admin_user: Any, request_factory: RequestFactory
    ) -> None:
        """Test bulk deletion with mixed results."""
        ContentType.objects.create(name='Без контента', code='empty', upload_folder='e')
        ct2 = ContentType.objects.create(name='С контентом2', code='full', upload_folder='f')
        Content.objects.create(title='Связанный', content_type=ct2)
        admin = ContentTypeAdmin(ContentType, site)
        request = get_request_with_messages(admin_user, request_factory)
        queryset = ContentType.objects.filter(code__in=['empty', 'full'])
        admin.delete_queryset(request, queryset)
        assert not ContentType.objects.filter(code='empty').exists()
        assert ContentType.objects.filter(code='full').exists()


@pytest.mark.django_db
class TestTagGroupAdmin:
    """Tests for TagGroupAdmin."""

    def test_get_categories_returns_all_when_empty(self, site: AdminSite) -> None:
        """Test get_categories returns 'Все' when no categories."""
        tg = TagGroup.objects.create(name='Группа без категорий')
        admin = TagGroupAdmin(TagGroup, site)
        assert admin.get_categories(tg) == 'Все'

    def test_get_categories_returns_category_names(self, site: AdminSite) -> None:
        """Test get_categories returns comma-separated names."""
        tg = TagGroup.objects.create(name='Группа с категориями')
        cat1 = Category.objects.create(name='Йога Тег', code='yoga_tag')
        cat2 = Category.objects.create(name='Ароматы Тег', code='aromas_tag')
        tg.categories.add(cat1, cat2)
        admin = TagGroupAdmin(TagGroup, site)
        result = admin.get_categories(tg)
        assert 'Йога Тег' in result
        assert 'Ароматы Тег' in result


@pytest.mark.django_db
class TestContentAdmin:
    """Tests for ContentAdmin."""

    def test_get_categories_returns_category_names(self, site: AdminSite) -> None:
        """Test get_categories returns comma-separated category names."""
        ct = ContentType.objects.create(name='Тип Админа', code='adm', upload_folder='adm')
        content = Content.objects.create(title='Тест Админ', content_type=ct)
        cat1 = Category.objects.create(name='Йога Контент', code='yoga_content')
        cat2 = Category.objects.create(name='Масла Контент', code='oils_content')
        content.categories.add(cat1, cat2)
        admin = ContentAdmin(Content, site)
        result = admin.get_categories(content)
        assert 'Йога Контент' in result
        assert 'Масла Контент' in result
