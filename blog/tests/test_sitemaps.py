"""Tests for sitemap functionality."""

import pytest
from django.test import Client

from blog.models import Content, ContentType
from blog.sitemaps import ContentSitemap, StaticViewSitemap


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


@pytest.mark.django_db
class TestContentSitemap:
    """Tests for ContentSitemap (covers lines 28, 45)."""

    def test_content_sitemap_lastmod(self) -> None:
        """Test lastmod returns updated_at (line 28)."""
        content_type, _ = ContentType.objects.get_or_create(
            code='video_sitemap', defaults={'name': 'Видео Sitemap'}
        )
        content = Content.objects.create(
            title='Sitemap Test',
            content_type=content_type,
        )
        sitemap = ContentSitemap()
        lastmod = sitemap.lastmod(content)
        assert lastmod == content.updated_at

    def test_content_sitemap_items(self) -> None:
        """Test items returns content queryset."""
        content_type, _ = ContentType.objects.get_or_create(
            code='video_sitemap2', defaults={'name': 'Видео Sitemap 2'}
        )
        Content.objects.create(
            title='Sitemap Item Test',
            content_type=content_type,
        )
        sitemap = ContentSitemap()
        items = sitemap.items()
        assert items.count() >= 1


@pytest.mark.django_db
class TestStaticViewSitemap:
    """Tests for StaticViewSitemap (covers line 45)."""

    def test_static_sitemap_location(self) -> None:
        """Test location returns correct paths (line 45)."""
        sitemap = StaticViewSitemap()
        assert sitemap.location('home') == '/'
        assert sitemap.location('search') == '/search/'
