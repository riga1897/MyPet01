import pytest
from django.test import Client


@pytest.mark.django_db
class TestHomeView:
    def test_home_returns_200(self) -> None:
        client = Client()
        response = client.get('/')
        assert response.status_code == 200

    def test_home_contains_welcome_message(self) -> None:
        client = Client()
        response = client.get('/')
        assert b'Welcome to MyPet01' in response.content

    def test_home_contains_admin_link(self) -> None:
        client = Client()
        response = client.get('/')
        assert b'/admin/' in response.content


