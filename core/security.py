"""Security utilities for the application.

Includes:
- Rate limiting decorators
- Honeypot form protection
- Input sanitization
- Security logging
"""
from __future__ import annotations

import logging
from functools import wraps
from typing import TYPE_CHECKING, Any

import bleach
from django.http import HttpResponseForbidden
from django_ratelimit.decorators import ratelimit

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse

HONEYPOT_FIELD_NAME = 'website_url'
ALLOWED_HTML_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's',
    'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'blockquote', 'code', 'pre',
]
ALLOWED_HTML_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],
    '*': ['class'],
}

security_logger = logging.getLogger('security')


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def log_security_event(
    event_type: str,
    request: HttpRequest,
    details: str = '',
    level: int = logging.WARNING,
) -> None:
    """Log security-related events."""
    ip = get_client_ip(request)
    user = getattr(request, 'user', None)
    username = user.username if user and user.is_authenticated else 'anonymous'
    path = request.path
    method = request.method

    message = f"[{event_type}] IP={ip} user={username} path={path} method={method}"
    if details:
        message += f" details={details}"

    security_logger.log(level, message)


def honeypot_check(
    view_func: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Decorator to check honeypot field in POST requests."""
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.method == 'POST':
            honeypot_value = request.POST.get(HONEYPOT_FIELD_NAME, '')
            if honeypot_value:
                log_security_event(
                    'HONEYPOT_TRIGGERED',
                    request,
                    f'field={HONEYPOT_FIELD_NAME} value={honeypot_value[:50]}',
                )
                return HttpResponseForbidden('Access denied.')
        return view_func(request, *args, **kwargs)
    return wrapper


def sanitize_html(content: str) -> str:
    """Sanitize HTML content, removing dangerous tags and scripts."""
    if not content:
        return content
    return bleach.clean(
        content,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True,
    )


def sanitize_text(content: str) -> str:
    """Strip all HTML tags from content."""
    if not content:
        return content
    return bleach.clean(content, tags=[], strip=True)


def rate_limit_login(
    view_func: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Rate limit decorator for login attempts."""
    return ratelimit(
        key='ip',
        rate='5/m',
        method='POST',
        block=True,
    )(view_func)


def rate_limit_upload(
    view_func: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Rate limit decorator for file uploads."""
    return ratelimit(
        key='user_or_ip',
        rate='20/m',
        method='POST',
        block=True,
    )(view_func)


def rate_limit_api(
    view_func: Callable[[HttpRequest], HttpResponse],
) -> Callable[[HttpRequest], HttpResponse]:
    """Rate limit decorator for API endpoints."""
    return ratelimit(
        key='user_or_ip',
        rate='60/m',
        method=['GET', 'POST'],
        block=True,
    )(view_func)


class HoneypotMiddleware:
    """Middleware to check honeypot field on all POST requests."""

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponse]
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == 'POST':
            honeypot_value = request.POST.get(HONEYPOT_FIELD_NAME, '')
            if honeypot_value:
                log_security_event(
                    'HONEYPOT_TRIGGERED',
                    request,
                    f'field={HONEYPOT_FIELD_NAME}',
                )
                return HttpResponseForbidden('Access denied.')
        return self.get_response(request)


class SecurityLoggingMiddleware:
    """Middleware to log suspicious requests."""

    SUSPICIOUS_PATTERNS = [
        '../',
        '..\\',
        '<script',
        'javascript:',
        'data:text/html',
        'onclick=',
        'onerror=',
    ]

    def __init__(
        self, get_response: Callable[[HttpRequest], HttpResponse]
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        self._check_suspicious_request(request)
        response = self.get_response(request)
        return response

    def _check_suspicious_request(self, request: HttpRequest) -> None:
        """Check for suspicious patterns in request."""
        path = request.path.lower()
        query = request.META.get('QUERY_STRING', '').lower()
        combined = path + query

        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.lower() in combined:
                log_security_event(
                    'SUSPICIOUS_REQUEST',
                    request,
                    f'pattern={pattern}',
                )
                break
