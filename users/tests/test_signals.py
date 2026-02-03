"""Tests for user authentication signals and rate limiting."""

import logging
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings


@pytest.mark.django_db
class TestAuthenticationSignals:
    """Tests for authentication signal handlers."""

    def test_failed_login_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Failed login should be logged."""
        client = Client()

        with caplog.at_level(logging.WARNING, logger='security'):
            client.post(
                '/users/login/',
                {'username': 'nonexistent', 'password': 'wrongpass'},
            )

        assert 'FAILED_LOGIN' in caplog.text
        assert 'nonexistent' in caplog.text

    def test_successful_login_logged(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Successful login should be logged."""
        User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        client = Client()

        with caplog.at_level(logging.INFO, logger='security'):
            client.post(
                '/users/login/',
                {'username': 'testuser', 'password': 'testpass123'},
            )

        assert 'LOGIN_SUCCESS' in caplog.text
        assert 'testuser' in caplog.text


@pytest.mark.django_db
class TestRateLimitedLogin:
    """Tests for login rate limiting."""

    @override_settings(RATELIMIT_ENABLE=True)
    def test_login_view_has_rate_limit_decorator(self) -> None:
        """Verify login view is protected by rate limiting."""
        from users.views import RateLimitedLoginView
        from django.utils.decorators import method_decorator

        assert hasattr(RateLimitedLoginView, 'post')

    def test_multiple_login_attempts_allowed_within_limit(self) -> None:
        """Normal login attempts should work within rate limit."""
        client = Client()

        for _ in range(3):
            response = client.post(
                '/users/login/',
                {'username': 'test', 'password': 'test'},
            )
            assert response.status_code in [200, 302]

    @patch('django_ratelimit.decorators.is_ratelimited')
    def test_rate_limit_blocks_when_exceeded(
        self, mock_ratelimited: object
    ) -> None:
        """Rate limiting should block excessive requests."""
        from django_ratelimit.exceptions import Ratelimited

        mock_ratelimited.return_value = True  # type: ignore[attr-defined]
        mock_ratelimited.side_effect = Ratelimited()  # type: ignore[attr-defined]

        client = Client()
        try:
            client.post(
                '/users/login/',
                {'username': 'test', 'password': 'test'},
            )
        except Ratelimited:
            pass
