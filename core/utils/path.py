"""Media path validation utilities."""

import os

from django.conf import settings


def safe_media_path(relative_path: str) -> str | None:
    """Validate and resolve a relative path within MEDIA_ROOT.

    Returns the full absolute path if valid, None if path traversal detected.
    Checks: no '..', no leading '/', resolved path stays within MEDIA_ROOT.
    """
    if not relative_path or '..' in relative_path or relative_path.startswith('/'):
        return None
    full_path = os.path.normpath(os.path.join(settings.MEDIA_ROOT, relative_path))
    media_root = os.path.normpath(str(settings.MEDIA_ROOT))
    if not full_path.startswith(media_root + os.sep):
        return None
    return full_path
