"""Tests for Content Security Policy headers."""

import pytest
from django.test import Client


@pytest.mark.django_db
class TestCSPHeaders:
    """Tests for CSP headers."""

    def test_csp_header_present(self, client: Client) -> None:
        """Test that CSP header is present in response."""
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers

    def test_csp_contains_default_src(self, client: Client) -> None:
        """Test that CSP contains default-src directive."""
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "default-src" in csp

    def test_csp_contains_script_src(self, client: Client) -> None:
        """Test that CSP contains script-src directive."""
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "script-src" in csp

    def test_csp_allows_tailwind_cdn(self, client: Client) -> None:
        """Test that CSP allows Tailwind CDN for development."""
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")
        assert "cdn.tailwindcss.com" in csp
