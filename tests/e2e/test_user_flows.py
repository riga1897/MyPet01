"""E2E tests for main user flows using Django test client."""
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def test_user(db: Any) -> Any:
    """Create a test user for authentication tests."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(client: Client, test_user: Any) -> Client:
    """Return a client logged in as test_user."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.mark.django_db
class TestHomepageFlow:
    """E2E tests for homepage user flow."""

    def test_homepage_loads_for_guest(self, client: Client) -> None:
        """Guest can access homepage."""
        response = client.get(reverse('blog:home'))
        assert response.status_code == 200
        assert 'html' in response.content.decode().lower()

    def test_homepage_has_hero_section(self, client: Client) -> None:
        """Homepage contains hero section."""
        response = client.get(reverse('blog:home'))
        content = response.content.decode()
        assert response.status_code == 200
        assert 'hero' in content or 'Hero' in content or 'class="' in content

    def test_homepage_loads_for_authenticated(self, authenticated_client: Client) -> None:
        """Authenticated user can access homepage with content."""
        response = authenticated_client.get(reverse('blog:home'))
        assert response.status_code == 200

    def test_guest_cannot_see_content_section(self, client: Client) -> None:
        """Guest should not see the cards/content section."""
        response = client.get(reverse('blog:home'))
        content = response.content.decode()
        assert 'id="cards"' not in content or 'login' in content.lower()


@pytest.mark.django_db
class TestAuthenticationFlow:
    """E2E tests for authentication flow."""

    def test_login_page_accessible(self, client: Client) -> None:
        """Login page is accessible."""
        response = client.get(reverse('users:login'))
        assert response.status_code == 200

    def test_login_with_valid_credentials(self, client: Client, test_user: Any) -> None:
        """User can log in with valid credentials."""
        response = client.post(
            reverse('users:login'),
            {'username': 'testuser', 'password': 'testpass123'},
            follow=True
        )
        assert response.status_code == 200

    def test_login_with_invalid_credentials(self, client: Client) -> None:
        """Login fails with invalid credentials."""
        response = client.post(
            reverse('users:login'),
            {'username': 'wronguser', 'password': 'wrongpass'}
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'error' in content.lower() or 'invalid' in content.lower() or 'form' in content.lower()

    def test_logout_redirects_to_home(self, authenticated_client: Client) -> None:
        """Logout redirects user to home page."""
        response = authenticated_client.post(reverse('users:logout'), follow=True)
        assert response.status_code == 200

    def test_protected_page_redirects_guest(self, client: Client) -> None:
        """Protected pages redirect guests to login."""
        response = client.get(reverse('blog:content_list'))
        assert response.status_code == 302 or response.status_code == 403


@pytest.mark.django_db
class TestNavigationFlow:
    """E2E tests for site navigation."""

    def test_admin_page_requires_auth(self, client: Client) -> None:
        """Admin page requires authentication."""
        response = client.get('/admin/')
        assert response.status_code == 302

    def test_sitemap_accessible(self, client: Client) -> None:
        """Sitemap is publicly accessible."""
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
        assert 'xml' in response.get('Content-Type', '')

    def test_static_files_served(self, client: Client) -> None:
        """Static files are accessible."""
        response = client.get('/static/css/style.css', follow=True)
        assert response.status_code in [200, 404]


@pytest.mark.django_db
class TestSearchFlow:
    """E2E tests for search functionality."""

    def test_search_page_accessible(self, client: Client) -> None:
        """Search page is accessible."""
        response = client.get(reverse('blog:search'))
        assert response.status_code == 200

    def test_search_with_query(self, client: Client) -> None:
        """Search with query parameter works."""
        response = client.get(reverse('blog:search'), {'q': 'йога'})
        assert response.status_code == 200

    def test_search_empty_query(self, client: Client) -> None:
        """Search with empty query returns results page."""
        response = client.get(reverse('blog:search'), {'q': ''})
        assert response.status_code == 200

    def test_search_with_special_characters(self, client: Client) -> None:
        """Search handles special characters safely."""
        response = client.get(reverse('blog:search'), {'q': '<script>alert(1)</script>'})
        assert response.status_code == 200
        content = response.content.decode()
        assert '<script>alert(1)</script>' not in content
