"""Tests for sitemap functionality."""

import pytest
from django.test import Client


@pytest.mark.django_db
class TestSitemap:
    """Tests for sitemap.xml endpoint."""

    def test_sitemap_returns_200(self, client: Client) -> None:
        """Test that sitemap.xml returns 200 status."""
        response = client.get("/sitemap.xml")
        assert response.status_code == 200

    def test_sitemap_content_type(self, client: Client) -> None:
        """Test that sitemap has correct content type."""
        response = client.get("/sitemap.xml")
        assert "xml" in response["Content-Type"]

    def test_sitemap_contains_home(self, client: Client) -> None:
        """Test that sitemap contains home page."""
        response = client.get("/sitemap.xml")
        content = response.content.decode("utf-8")
        assert "<loc>" in content
        assert "/" in content
