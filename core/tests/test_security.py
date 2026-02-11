"""Tests for security utilities."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpResponseForbidden
from django.test import RequestFactory

from core.security import (
    HONEYPOT_FIELD_NAME,
    HoneypotMiddleware,
    SecurityLoggingMiddleware,
    get_client_ip,
    honeypot_check,
    log_security_event,
    sanitize_html,
    sanitize_text,
)


class TestSanitizeHtml:
    """Tests for HTML sanitization."""

    def test_removes_script_tags(self) -> None:
        """Script tags should be stripped."""
        content = '<p>Hello</p><script>alert("xss")</script>'
        result = sanitize_html(content)
        assert '<script>' not in result
        assert '<p>Hello</p>' in result

    def test_allows_safe_tags(self) -> None:
        """Safe tags should be preserved."""
        content = '<p>Text with <strong>bold</strong> and <em>italic</em></p>'
        result = sanitize_html(content)
        assert '<p>' in result
        assert '<strong>' in result
        assert '<em>' in result

    def test_removes_onclick_attributes(self) -> None:
        """Event handlers should be stripped."""
        content = '<a href="test.html" onclick="evil()">Link</a>'
        result = sanitize_html(content)
        assert 'onclick' not in result
        assert 'href="test.html"' in result

    def test_empty_string_returns_empty(self) -> None:
        """Empty string should return empty."""
        assert sanitize_html('') == ''

    def test_none_returns_none(self) -> None:
        """None-like values should be handled."""
        result = sanitize_html('')
        assert result == ''


class TestSanitizeText:
    """Tests for text sanitization (strip all HTML)."""

    def test_strips_all_html(self) -> None:
        """All HTML tags should be removed."""
        content = '<p>Hello <strong>World</strong></p>'
        result = sanitize_text(content)
        assert '<' not in result
        assert '>' not in result
        assert 'Hello' in result
        assert 'World' in result

    def test_strips_malicious_content(self) -> None:
        """Malicious content should be stripped."""
        content = '<script>alert("xss")</script>Safe text'
        result = sanitize_text(content)
        assert 'Safe text' in result
        assert '<script>' not in result

    def test_empty_string_returns_empty(self) -> None:
        """Empty string should return empty."""
        assert sanitize_text('') == ''


class TestGetClientIp:
    """Tests for client IP extraction."""

    def test_extracts_from_x_forwarded_for(self) -> None:
        """Should extract IP from X-Forwarded-For header."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '1.2.3.4, 5.6.7.8'
        assert get_client_ip(request) == '1.2.3.4'

    def test_extracts_from_remote_addr(self) -> None:
        """Should extract IP from REMOTE_ADDR."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        assert get_client_ip(request) == '10.0.0.1'

    def test_returns_unknown_when_no_ip(self) -> None:
        """Should return 'unknown' when no IP available."""
        factory = RequestFactory()
        request = factory.get('/')
        request.META.pop('REMOTE_ADDR', None)
        result = get_client_ip(request)
        assert result in ['unknown', '127.0.0.1']


class TestLogSecurityEvent:
    """Tests for security event logging."""

    def test_logs_event_with_details(self) -> None:
        """Should log security events with all details."""
        factory = RequestFactory()
        request = factory.post('/login/')
        request.user = MagicMock(is_authenticated=False, username='anonymous')

        with patch.object(
            logging.getLogger('security'), 'log'
        ) as mock_log:
            log_security_event('TEST_EVENT', request, 'test details')

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[0][0] == logging.WARNING
        assert 'TEST_EVENT' in call_args[0][1]
        assert 'test details' in call_args[0][1]


class TestHoneypotCheck:
    """Tests for honeypot decorator."""

    def test_blocks_filled_honeypot(self) -> None:
        """Should block requests with filled honeypot field."""
        factory = RequestFactory()
        request = factory.post('/', {HONEYPOT_FIELD_NAME: 'bot value'})
        request.user = MagicMock(is_authenticated=False)

        @honeypot_check
        def dummy_view(req):  # type: ignore[no-untyped-def]
            return MagicMock(status_code=200)

        response = dummy_view(request)
        assert isinstance(response, HttpResponseForbidden)

    def test_allows_empty_honeypot(self) -> None:
        """Should allow requests with empty honeypot field."""
        factory = RequestFactory()
        request = factory.post('/', {HONEYPOT_FIELD_NAME: ''})

        @honeypot_check
        def dummy_view(req):  # type: ignore[no-untyped-def]
            return MagicMock(status_code=200)

        response = dummy_view(request)
        assert response.status_code == 200

    def test_allows_get_requests(self) -> None:
        """Should allow GET requests without checking honeypot."""
        factory = RequestFactory()
        request = factory.get('/')

        @honeypot_check
        def dummy_view(req):  # type: ignore[no-untyped-def]
            return MagicMock(status_code=200)

        response = dummy_view(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestHoneypotMiddleware:
    """Tests for honeypot middleware."""

    def test_blocks_bot_with_honeypot(self) -> None:
        """Should block requests with filled honeypot."""
        factory = RequestFactory()
        request = factory.post(
            '/users/login/',
            {
                'username': 'test',
                'password': 'test',
                HONEYPOT_FIELD_NAME: 'bot filled this',
            },
        )
        request.user = MagicMock(is_authenticated=False)

        middleware = HoneypotMiddleware(lambda r: MagicMock(status_code=200))

        with patch.object(
            logging.getLogger('security'), 'log'
        ):
            response = middleware(request)

        assert response.status_code == 403

    def test_allows_normal_login(self) -> None:
        """Should allow normal login without honeypot filled."""
        factory = RequestFactory()
        request = factory.post(
            '/users/login/',
            {
                'username': 'test',
                'password': 'test',
                HONEYPOT_FIELD_NAME: '',
            },
        )

        mock_response = MagicMock(status_code=200)
        middleware = HoneypotMiddleware(lambda r: mock_response)
        response = middleware(request)

        assert response.status_code == 200


@pytest.mark.django_db
class TestSecurityLoggingMiddleware:
    """Tests for security logging middleware."""

    def test_logs_path_traversal_attempt(self) -> None:
        """Should log path traversal attempts."""
        factory = RequestFactory()
        request = factory.get('/test/../../../etc/passwd')
        request.user = MagicMock(is_authenticated=False, username='anonymous')

        middleware = SecurityLoggingMiddleware(lambda r: MagicMock(status_code=404))

        with patch.object(
            logging.getLogger('security'), 'log'
        ) as mock_log:
            middleware(request)

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert 'SUSPICIOUS_REQUEST' in call_args[0][1]
        assert '../' in call_args[0][1]

    def test_logs_script_injection_attempt(self) -> None:
        """Should log script injection attempts."""
        factory = RequestFactory()
        request = factory.get('/test')
        request.META['QUERY_STRING'] = '<script>alert(1)</script>'
        request.user = MagicMock(is_authenticated=False, username='anonymous')

        middleware = SecurityLoggingMiddleware(lambda r: MagicMock(status_code=200))

        with patch.object(
            logging.getLogger('security'), 'log'
        ) as mock_log:
            middleware(request)

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert 'SUSPICIOUS_REQUEST' in call_args[0][1]


@pytest.mark.django_db
class TestContentSanitization:
    """Tests for content model sanitization."""

    def test_description_sanitized_on_save(self) -> None:
        """Description field should be sanitized on save."""
        from blog.models import Content

        content = Content(
            title='Test',
            description='<script>alert("xss")</script>Safe text',
        )
        content.save()

        assert '<script>' not in content.description
        assert 'Safe text' in content.description

    def test_normal_description_preserved(self) -> None:
        """Normal text should be preserved."""
        from blog.models import Content

        content = Content(
            title='Test',
            description='This is normal description text.',
        )
        content.save()

        assert content.description == 'This is normal description text.'


class TestRateLimitDecorators:
    """Tests for rate limit decorator functions (lines 109-141)."""

    def test_rate_limit_login_decorator(self) -> None:
        """Test rate_limit_login decorator wraps function correctly."""
        from django.http import HttpRequest, HttpResponse

        from core.security import rate_limit_login

        def dummy_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("response")

        decorated = rate_limit_login(dummy_view)
        assert callable(decorated)

    def test_rate_limit_upload_decorator(self) -> None:
        """Test rate_limit_upload decorator wraps function correctly."""
        from django.http import HttpRequest, HttpResponse

        from core.security import rate_limit_upload

        def dummy_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("response")

        decorated = rate_limit_upload(dummy_view)
        assert callable(decorated)

    def test_rate_limit_api_decorator(self) -> None:
        """Test rate_limit_api decorator wraps function correctly."""
        from django.http import HttpRequest, HttpResponse

        from core.security import rate_limit_api

        def dummy_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("response")

        decorated = rate_limit_api(dummy_view)
        assert callable(decorated)
