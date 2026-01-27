"""Locust load testing configuration for MyPet01.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:5000

Or headless:
    locust -f tests/load/locustfile.py --host=http://localhost:5000 \
        --headless -u 10 -r 2 --run-time 60s
"""
from locust import HttpUser, between, task


class GuestUser(HttpUser):
    """Simulates a guest user browsing the site."""

    wait_time = between(1, 3)

    @task(10)
    def view_homepage(self) -> None:
        """Load the homepage - most common action."""
        self.client.get('/', name='Homepage')

    @task(3)
    def view_sitemap(self) -> None:
        """Load sitemap for SEO crawlers."""
        self.client.get('/sitemap.xml', name='Sitemap')

    @task(2)
    def search_content(self) -> None:
        """Search for content."""
        self.client.get('/search/?q=йога', name='Search - yoga')

    @task(2)
    def search_with_typo(self) -> None:
        """Search with typo to test fuzzy search."""
        self.client.get('/search/?q=йго', name='Search - typo')

    @task(1)
    def search_wrong_layout(self) -> None:
        """Search with wrong keyboard layout."""
        self.client.get('/search/?q=qjuf', name='Search - wrong layout')

    @task(1)
    def view_login_page(self) -> None:
        """View login page."""
        self.client.get('/users/login/', name='Login page')


class AuthenticatedUser(HttpUser):
    """Simulates an authenticated user."""

    wait_time = between(1, 5)

    def on_start(self) -> None:
        """Login at the start of the session."""
        self.client.get('/users/login/')
        response = self.client.post(
            '/users/login/',
            {
                'username': 'loadtest',
                'password': 'loadtest123',
                'csrfmiddlewaretoken': self._get_csrf_token()
            },
            name='Login POST'
        )
        if response.status_code != 200:
            pass

    def _get_csrf_token(self) -> str:
        """Extract CSRF token from cookies."""
        return self.client.cookies.get('csrftoken', '')

    @task(10)
    def view_homepage_authenticated(self) -> None:
        """Load homepage as authenticated user."""
        self.client.get('/', name='Homepage (auth)')

    @task(5)
    def search_content(self) -> None:
        """Search for content."""
        self.client.get('/search/?q=масла', name='Search - oils (auth)')

    @task(2)
    def view_moderator_panel(self) -> None:
        """Try to access moderator panel."""
        self.client.get('/moderator/', name='Moderator panel')


class APIUser(HttpUser):
    """Simulates API endpoint usage."""

    wait_time = between(0.5, 2)

    @task(5)
    def check_category_code(self) -> None:
        """Check category code availability API."""
        self.client.get(
            '/api/check-category-code/?code=test',
            name='API - Check category code'
        )

    @task(5)
    def check_content_type_code(self) -> None:
        """Check content type code availability API."""
        self.client.get(
            '/api/check-content-type-code/?code=video',
            name='API - Check content type code'
        )

    @task(3)
    def check_content_type_folder(self) -> None:
        """Check content type folder availability API."""
        self.client.get(
            '/api/check-content-type-folder/?folder=videos',
            name='API - Check folder'
        )

    @task(2)
    def get_available_files(self) -> None:
        """Get available files for content type."""
        self.client.get(
            '/api/available-files/?folder=videos',
            name='API - Available files'
        )

    @task(2)
    def get_available_thumbnails(self) -> None:
        """Get available thumbnails."""
        self.client.get(
            '/api/available-thumbnails/',
            name='API - Available thumbnails'
        )


class MixedUser(HttpUser):
    """Simulates a typical mixed user behavior."""

    wait_time = between(2, 5)
    weight = 3

    @task(20)
    def browse_homepage(self) -> None:
        """Browse homepage."""
        self.client.get('/', name='Mixed - Homepage')

    @task(10)
    def search(self) -> None:
        """Perform search."""
        queries = ['йога', 'масла', 'медитация', 'здоровье']
        import random
        q = random.choice(queries)
        self.client.get(f'/search/?q={q}', name=f'Mixed - Search')

    @task(5)
    def view_sitemap(self) -> None:
        """View sitemap."""
        self.client.get('/sitemap.xml', name='Mixed - Sitemap')

    @task(1)
    def check_api(self) -> None:
        """Check API endpoint."""
        self.client.get(
            '/api/check-category-code/?code=test',
            name='Mixed - API'
        )
