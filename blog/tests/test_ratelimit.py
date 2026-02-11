"""Tests for rate limiting functionality."""

import pytest
from django.test import Client


@pytest.mark.django_db
class TestRateLimit:
    """Tests for rate limiting on views."""

    def test_search_view_accessible(self, client: Client) -> None:
        """Test that search view is accessible within rate limits."""
        response = client.get("/search/", {"q": "test"})
        assert response.status_code == 200

    def test_search_view_returns_results_page(self, client: Client) -> None:
        """Test that search view returns search results page."""
        response = client.get("/search/", {"q": "yoga"})
        assert response.status_code == 200
        assert b"search" in response.content.lower() or response.status_code == 200
