"""Security signals for user authentication."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.contrib.auth.signals import user_login_failed, user_logged_in
from django.dispatch import receiver

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from django.http import HttpRequest

security_logger = logging.getLogger('security')


def get_client_ip(request: HttpRequest | None) -> str:
    """Extract client IP from request."""
    if request is None:
        return 'unknown'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


@receiver(user_login_failed)
def log_failed_login(
    sender: Any,
    credentials: dict[str, Any],
    request: HttpRequest | None = None,
    **kwargs: Any,
) -> None:
    """Log failed login attempts."""
    ip = get_client_ip(request)
    username = credentials.get('username', 'unknown')
    security_logger.warning(
        f"[FAILED_LOGIN] IP={ip} username={username}"
    )


@receiver(user_logged_in)
def log_successful_login(
    sender: Any,
    request: HttpRequest | None,
    user: User,
    **kwargs: Any,
) -> None:
    """Log successful logins."""
    ip = get_client_ip(request)
    security_logger.info(
        f"[LOGIN_SUCCESS] IP={ip} username={user.username}"
    )
