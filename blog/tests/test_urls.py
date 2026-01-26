import pytest
from django.test import Client


@pytest.mark.django_db
class TestBlogUrls:
    def test_home_returns_200(self) -> None:
        client = Client()
        response = client.get('/')
        assert response.status_code == 200

    def test_home_uses_correct_template(self) -> None:
        client = Client()
        response = client.get('/')
        assert 'blog/index.html' in [t.name for t in response.templates]

    def test_home_contains_blog_title(self) -> None:
        client = Client()
        response = client.get('/')
        assert 'Гармония Души' in response.content.decode('utf-8')

    def test_home_contains_cards_section(self) -> None:
        client = Client()
        response = client.get('/')
        assert 'id="cards"' in response.content.decode('utf-8')
