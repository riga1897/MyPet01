"""Sitemap configuration for blog content."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from django.contrib.sitemaps import Sitemap

from blog.models import Content

if TYPE_CHECKING:
    from django.db.models import QuerySet


class ContentSitemap(Sitemap):  # type: ignore[type-arg]
    """Sitemap for Content items."""

    changefreq = "weekly"
    priority = 0.8

    def items(self) -> QuerySet[Content]:
        """Return all published content items."""
        return Content.objects.all()

    def lastmod(self, obj: Content) -> datetime:
        """Return last modification date."""
        return obj.updated_at


class StaticViewSitemap(Sitemap):  # type: ignore[type-arg]
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
