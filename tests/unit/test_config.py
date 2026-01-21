from mypet_project.config import Settings


class TestSettings:
    def test_get_database_url_returns_database_url_when_set(self) -> None:
        settings = Settings(database_url='postgres://user:pass@host:5432/db')
        assert settings.get_database_url() == 'postgres://user:pass@host:5432/db'

    def test_get_database_url_builds_from_postgres_vars(self) -> None:
        settings = Settings(
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
            database_url='',
            postgres_user='',
            postgres_password='',
            postgres_db='',
        )
        assert settings.get_database_url() == ''

    def test_allowed_hosts_list_splits_correctly(self) -> None:
        settings = Settings(allowed_hosts='host1.com, host2.com, host3.com')
        assert settings.allowed_hosts_list == ['host1.com', 'host2.com', 'host3.com']

    def test_csrf_trusted_origins_list_splits_correctly(self) -> None:
        settings = Settings(csrf_trusted_origins='https://a.com, https://b.com')
        assert settings.csrf_trusted_origins_list == ['https://a.com', 'https://b.com']
