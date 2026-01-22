"""Tests for middleware."""
from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase, override_settings


class BrowserCacheMiddlewareTestCase(TestCase):
    """Tests for BrowserCacheMiddleware."""

    def test_no_cache_headers_when_disabled(self) -> None:
        """Test that no-cache headers are added when browser cache is disabled."""
        with patch('mypet_project.config.settings.browser_cache_enabled', False):
            response = self.client.get('/')

        self.assertIn('no-cache', response.get('Cache-Control', ''))

    def test_cache_headers_for_static_when_enabled(self) -> None:
        """Test that cache headers are added for static files when enabled."""
        with patch('mypet_project.config.settings.browser_cache_enabled', True), \
             patch('mypet_project.config.settings.browser_cache_max_age', 3600):
            response = self.client.get('/static/favicon.png')

        cache_control = response.get('Cache-Control', '')
        self.assertIn('max-age=3600', cache_control)

    def test_dynamic_pages_get_no_cache_when_enabled(self) -> None:
        """Test that dynamic pages get no-cache headers when browser cache is enabled."""
        with patch('mypet_project.config.settings.browser_cache_enabled', True):
            response = self.client.get('/')

        cache_control = response.get('Cache-Control', '')
        self.assertIn('no-cache', cache_control)

    def test_home_page_accessible(self) -> None:
        """Test that home page is accessible with middleware."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
