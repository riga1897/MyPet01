import pytest
from django.urls import reverse
from rest_framework import status
from django.test import Client


@pytest.mark.django_db
def test_admin_page_load(client: Client) -> None:
    url = reverse('admin:index')
    response = client.get(url)
    # Redirect to login is expected for unauthenticated user
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]
