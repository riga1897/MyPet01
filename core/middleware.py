"""Custom middleware for the application."""
from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Callable

from django.conf import settings
from django.utils.cache import add_never_cache_headers

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

from mypet_project.config import settings as env_settings


class BrowserCacheMiddleware:
    """Middleware to control browser caching via Cache-Control headers."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        if not env_settings.browser_cache_enabled:
            add_never_cache_headers(response)
        elif self._is_static_request(request):
            max_age = env_settings.browser_cache_max_age
            response['Cache-Control'] = f'public, max-age={max_age}'
        else:
            add_never_cache_headers(response)

        return response

    def _is_static_request(self, request: HttpRequest) -> bool:
        """Check if request is for static or media files."""
        path = request.path
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        return path.startswith(static_url) or path.startswith(media_url)
