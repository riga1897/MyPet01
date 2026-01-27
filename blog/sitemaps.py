"""Sitemap configuration for blog content."""

from django.contrib.sitemaps import Sitemap

from blog.models import Content


class ContentSitemap(Sitemap):
    """Sitemap for Content items."""

    changefreq = "weekly"
    priority = 0.8

    def items(self) -> list[Content]:
        """Return all published content items."""
        return list(Content.objects.all())

    def lastmod(self, obj: Content):
        """Return last modification date."""
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""

    priority = 1.0
    changefreq = "daily"

    def items(self) -> list[str]:
        """Return list of static page names."""
        return ["home"]

    def location(self, item: str) -> str:
        """Return URL for static page."""
        if item == "home":
            return "/"
        return f"/{item}/"
