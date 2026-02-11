import pytest
from django.contrib.auth.models import User
from django.test import Client

from users.models import get_or_create_moderators_group


@pytest.mark.django_db
class TestLoginView:
    def test_login_page_returns_200(self) -> None:
        client = Client()
        response = client.get('/users/login/')
        assert response.status_code == 200

    def test_login_page_uses_correct_template(self) -> None:
        client = Client()
        response = client.get('/users/login/')
        assert 'users/login.html' in [t.name for t in response.templates]

    def test_successful_login_redirects_to_home(self) -> None:
        User.objects.create_user(username='testuser', password='testpass123')
        client = Client()
        response = client.post('/users/login/', {
            'username': 'testuser',
            'password': 'testpass123',
            'website_url': '',
        })
        assert response.status_code == 302
        assert response.url == '/'  # type: ignore[attr-defined]

    def test_failed_login_shows_error(self) -> None:
        client = Client()
        response = client.post('/users/login/', {
            'username': 'nonexistent',
            'password': 'wrongpass',
            'website_url': '',
        })
        assert response.status_code == 200
        assert 'Неверное имя пользователя или пароль' in response.content.decode('utf-8')


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_redirects_to_home(self) -> None:
        user = User.objects.create_user(username='testuser', password='testpass123')
        client = Client()
        client.force_login(user)
        response = client.post('/users/logout/')
        assert response.status_code == 302
        assert response.url == '/'  # type: ignore[attr-defined]


@pytest.mark.django_db
class TestModeratorListView:
    def test_anonymous_user_redirected_to_login(self) -> None:
        client = Client()
        response = client.get('/users/moderators/')
        assert response.status_code == 302
        assert '/users/login/' in response.url  # type: ignore[attr-defined]

    def test_regular_user_gets_403(self) -> None:
        user = User.objects.create_user(username='regular', password='test123')
        client = Client()
        client.force_login(user)
        response = client.get('/users/moderators/')
        assert response.status_code == 403

    def test_moderator_gets_403(self) -> None:
        """Moderator (non-superuser) cannot access moderator management."""
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        client = Client()
        client.force_login(user)
        response = client.get('/users/moderators/')
        assert response.status_code == 403

    def test_superuser_can_access(self) -> None:
        user = User.objects.create_superuser(username='admin', password='test123')
        client = Client()
        client.force_login(user)
        response = client.get('/users/moderators/')
        assert response.status_code == 200

    def test_shows_all_users(self) -> None:
        admin = User.objects.create_superuser(username='admin', password='test123')
        User.objects.create_user(username='user1', password='test123')
        User.objects.create_user(username='user2', password='test123')
        client = Client()
        client.force_login(admin)
        response = client.get('/users/moderators/')
        content = response.content.decode('utf-8')
        assert 'user1' in content
        assert 'user2' in content


@pytest.mark.django_db
class TestAddModerator:
    def test_anonymous_user_redirected(self) -> None:
        user = User.objects.create_user(username='target', password='test123')
        client = Client()
        response = client.post(f'/users/moderators/add/{user.pk}/')
        assert response.status_code == 302
        assert '/users/login/' in response.url  # type: ignore[attr-defined]

    def test_regular_user_gets_403(self) -> None:
        regular = User.objects.create_user(username='regular', password='test123')
        target = User.objects.create_user(username='target', password='test123')
        client = Client()
        client.force_login(regular)
        response = client.post(f'/users/moderators/add/{target.pk}/')
        assert response.status_code == 302
        assert '/users/login/' in response.url  # type: ignore[attr-defined]

    def test_moderator_cannot_add_user(self) -> None:
        """Moderator (non-superuser) cannot add users to moderators group."""
        mod = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        mod.groups.add(group)
        target = User.objects.create_user(username='target', password='test123')
        client = Client()
        client.force_login(mod)
        response = client.post(f'/users/moderators/add/{target.pk}/')
        assert response.status_code == 302
        assert '/users/login/' in response.url  # type: ignore[attr-defined]
        target.refresh_from_db()
        assert not target.groups.filter(name='Модераторы').exists()

    def test_superuser_can_add_user(self) -> None:
        """Superuser can add users to moderators group."""
        admin = User.objects.create_superuser(username='admin', password='test123')
        target = User.objects.create_user(username='target', password='test123')
        client = Client()
        client.force_login(admin)
        response = client.post(f'/users/moderators/add/{target.pk}/')
        assert response.status_code == 302
        target.refresh_from_db()
        assert target.groups.filter(name='Модераторы').exists()

    def test_get_request_does_not_add(self) -> None:
        admin = User.objects.create_superuser(username='admin', password='test123')
        target = User.objects.create_user(username='target', password='test123')
        client = Client()
        client.force_login(admin)
        client.get(f'/users/moderators/add/{target.pk}/')
        target.refresh_from_db()
        assert not target.groups.filter(name='Модераторы').exists()


@pytest.mark.django_db
class TestRemoveModerator:
    def test_moderator_cannot_remove_user(self) -> None:
        """Moderator (non-superuser) cannot remove users from moderators group."""
        mod = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        mod.groups.add(group)
        target = User.objects.create_user(username='target', password='test123')
        target.groups.add(group)
        client = Client()
        client.force_login(mod)
        response = client.post(f'/users/moderators/remove/{target.pk}/')
        assert response.status_code == 302
        assert '/users/login/' in response.url  # type: ignore[attr-defined]
        target.refresh_from_db()
        assert target.groups.filter(name='Модераторы').exists()

    def test_superuser_can_remove_user(self) -> None:
        """Superuser can remove users from moderators group."""
        admin = User.objects.create_superuser(username='admin', password='test123')
        target = User.objects.create_user(username='target', password='test123')
        group = get_or_create_moderators_group()
        target.groups.add(group)
        client = Client()
        client.force_login(admin)
        response = client.post(f'/users/moderators/remove/{target.pk}/')
        assert response.status_code == 302
        target.refresh_from_db()
        assert not target.groups.filter(name='Модераторы').exists()

    def test_get_request_does_not_remove(self) -> None:
        admin = User.objects.create_superuser(username='admin', password='test123')
        target = User.objects.create_user(username='target', password='test123')
        group = get_or_create_moderators_group()
        target.groups.add(group)
        client = Client()
        client.force_login(admin)
        client.get(f'/users/moderators/remove/{target.pk}/')
        target.refresh_from_db()
        assert target.groups.filter(name='Модераторы').exists()
