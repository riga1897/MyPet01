"""Context processors for global template variables."""

from typing import Any

from django.http import HttpRequest

from users.models import is_moderator


def user_permissions(request: HttpRequest) -> dict[str, Any]:
    """Add user permission flags to template context."""
    return {
        "is_moderator": is_moderator(request.user),
    }
