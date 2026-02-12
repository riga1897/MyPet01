"""Tests for core.utils.path module."""

import os

from django.conf import settings

from core.utils.path import safe_media_path


class TestSafeMediaPath:
    """Tests for safe_media_path utility."""

    def test_valid_relative_path(self) -> None:
        result = safe_media_path('thumbnails/test.jpg')
        expected = os.path.normpath(
            os.path.join(settings.MEDIA_ROOT, 'thumbnails/test.jpg')
        )
        assert result == expected

    def test_valid_simple_path(self) -> None:
        result = safe_media_path('video/file.mp4')
        assert result is not None
        assert result.endswith(os.path.join('video', 'file.mp4'))

    def test_empty_path_returns_none(self) -> None:
        assert safe_media_path('') is None

    def test_path_with_dotdot_returns_none(self) -> None:
        assert safe_media_path('../etc/passwd') is None
        assert safe_media_path('thumbnails/../../secret') is None

    def test_path_starting_with_slash_returns_none(self) -> None:
        assert safe_media_path('/etc/passwd') is None
        assert safe_media_path('/absolute/path') is None

    def test_path_resolving_to_media_root_returns_none(self) -> None:
        assert safe_media_path('.') is None

    def test_folder_only(self) -> None:
        result = safe_media_path('thumbnails')
        assert result is not None
        assert result.endswith('thumbnails')
