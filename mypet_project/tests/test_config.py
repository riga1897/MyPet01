from mypet_project.config import Settings


class TestSettings:
    def test_get_database_url_returns_database_url_when_set(self) -> None:
        settings = Settings(django_env='development', database_url='postgres://user:pass@host:5432/db')
        assert settings.get_database_url() == 'postgres://user:pass@host:5432/db'

    def test_get_database_url_builds_from_postgres_vars(self) -> None:
        settings = Settings(
            django_env='development',
            database_url='',
            postgres_user='testuser',
            postgres_password='testpass',
            postgres_host='testhost',
            postgres_port='5433',
            postgres_db='testdb',
        )
        expected = 'postgres://testuser:testpass@testhost:5433/testdb'
        assert settings.get_database_url() == expected

    def test_get_database_url_returns_empty_when_no_config(self) -> None:
        settings = Settings(
            django_env='development',
            database_url='',
            postgres_user='',
            postgres_password='',
            postgres_db='',
        )
        assert settings.get_database_url() == ''

    def test_allowed_hosts_list_splits_correctly(self) -> None:
        settings = Settings(django_env='development', allowed_hosts='host1.com, host2.com, host3.com')
        assert settings.allowed_hosts_list == ['host1.com', 'host2.com', 'host3.com']

    def test_csrf_trusted_origins_list_splits_correctly(self) -> None:
        settings = Settings(django_env='development', csrf_trusted_origins='https://a.com, https://b.com')
        assert settings.csrf_trusted_origins_list == ['https://a.com', 'https://b.com']

    def test_production_security_defaults(self) -> None:
        settings = Settings(django_env='development')
        assert settings.is_secure_ssl_redirect is False
        assert settings.get_secure_hsts_seconds == 0
        assert settings.is_secure_hsts_include_subdomains is False
        assert settings.is_secure_hsts_preload is False
        assert settings.is_session_cookie_secure is False
        assert settings.is_csrf_cookie_secure is False
        assert settings.secure_browser_xss_filter is True
        assert settings.secure_content_type_nosniff is True
        assert settings.x_frame_options == 'DENY'

    def test_production_security_use_https_toggle(self) -> None:
        settings = Settings(django_env='development', use_https=True, csrf_cookie_secure=None)
        assert settings.is_secure_ssl_redirect is True
        assert settings.get_secure_hsts_seconds == 31536000
        assert settings.is_secure_hsts_include_subdomains is True
        assert settings.is_secure_hsts_preload is True
        assert settings.is_session_cookie_secure is True
        assert settings.is_csrf_cookie_secure is True

    def test_production_security_can_be_overridden(self) -> None:
        settings = Settings(
            django_env='development',
            use_https=True,
            secure_ssl_redirect=False,
            secure_hsts_seconds=60
        )
        assert settings.is_secure_ssl_redirect is False
        assert settings.get_secure_hsts_seconds == 60
        assert settings.is_session_cookie_secure is True

    def test_admin_show_facets_defaults_to_true(self) -> None:
        settings = Settings(django_env='development')
        assert settings.admin_show_facets is True

    def test_admin_show_facets_can_be_disabled(self) -> None:
        settings = Settings(django_env='development', admin_show_facets=False)
        assert settings.admin_show_facets is False
