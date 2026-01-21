from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    debug: bool = False
    secret_key: str = 'django-insecure-dummy-key'
    allowed_hosts: str = '*'

    database_url: str = ''
    postgres_user: str = ''
    postgres_password: str = ''
    postgres_host: str = 'localhost'
    postgres_port: str = '5432'
    postgres_db: str = ''

    csrf_trusted_origins: str = 'https://*.replit.dev,https://*.repl.co,https://*.pike.replit.dev'
    csrf_cookie_secure: bool = False
    csrf_cookie_httponly: bool = True
    csrf_cookie_samesite: str = 'Lax'

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(',') if h.strip()]

    @property
    def csrf_trusted_origins_list(self) -> list[str]:
        return [o.strip() for o in self.csrf_trusted_origins.split(',') if o.strip()]

    def get_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.postgres_user and self.postgres_password and self.postgres_db:
            return (
                f"postgres://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return ''


settings = Settings()
