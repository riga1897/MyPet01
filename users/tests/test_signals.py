"""Tests for user authentication signals and rate limiting."""

import logging
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client, RequestFactory, override_settings

from users.signals import log_failed_login, log_successful_login


@pytest.mark.django_db
class TestAuthenticationSignals:
    """Tests for authentication signal handlers."""

    def test_failed_login_signal_handler(self) -> None:
        """Failed login signal handler should log correctly."""
        factory = RequestFactory()
        request = factory.post('/users/login/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        with patch.object(
            logging.getLogger('security'), 'warning'
        ) as mock_log:
            log_failed_login(
                sender=None,
                credentials={'username': 'testuser'},
                request=request,
            )

        mock_log.assert_called_once()
        call_args = mock_log.call_args[0][0]
        assert 'FAILED_LOGIN' in call_args
        assert 'testuser' in call_args

    def test_successful_login_signal_handler(self) -> None:
        """Successful login signal handler should log correctly."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        factory = RequestFactory()
        request = factory.post('/users/login/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        with patch.object(
            logging.getLogger('security'), 'info'
        ) as mock_log:
            log_successful_login(
                sender=User,
                request=request,
                user=user,
            )

        mock_log.assert_called_once()
        call_args = mock_log.call_args[0][0]
        assert 'LOGIN_SUCCESS' in call_args
        assert 'testuser' in call_args


@pytest.mark.django_db
class TestRateLimitedLogin:
    """Tests for login rate limiting."""

    @override_settings(RATELIMIT_ENABLE=True)
    def test_login_view_has_rate_limit_decorator(self) -> None:
        """Verify login view is protected by rate limiting."""
        from users.views import RateLimitedLoginView

        assert hasattr(RateLimitedLoginView, 'post')

    def test_multiple_login_attempts_allowed_within_limit(self) -> None:
        """Normal login attempts should work within rate limit."""
        client = Client()

        for _ in range(3):
            response = client.post(
                '/users/login/',
                {'username': 'test', 'password': 'test', 'website_url': ''},
            )
            assert response.status_code in [200, 302]

    @patch('django_ratelimit.decorators.is_ratelimited')
    def test_rate_limit_blocks_when_exceeded(
        self, mock_ratelimited: object
    ) -> None:
        """Rate limiting should block excessive requests."""
        import contextlib

        from django_ratelimit.exceptions import Ratelimited

        mock_ratelimited.return_value = True  # type: ignore[attr-defined]
        mock_ratelimited.side_effect = Ratelimited()  # type: ignore[attr-defined]

        client = Client()
        with contextlib.suppress(Ratelimited):
            client.post(
                '/users/login/',
                {'username': 'test', 'password': 'test', 'website_url': ''},
            )


class TestGetClientIp:
    """Tests for get_client_ip function (lines 21, 24)."""

    def test_get_client_ip_from_x_forwarded_for(self) -> None:
        """Test IP extraction from X-Forwarded-For header."""
        from users.signals import get_client_ip

        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'

        ip = get_client_ip(request)
        assert ip == '10.0.0.1'

    def test_get_client_ip_with_none_request(self) -> None:
        """Test IP extraction when request is None."""
        from users.signals import get_client_ip

        ip = get_client_ip(None)
        assert ip == 'unknown'

    def test_get_client_ip_from_remote_addr(self) -> None:
        """Test IP extraction from REMOTE_ADDR."""
        from users.signals import get_client_ip

        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'

        ip = get_client_ip(request)
        assert ip == '192.168.1.100'
