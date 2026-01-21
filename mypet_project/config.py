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
    csrf_cookie_secure: bool | None = None
    csrf_cookie_httponly: bool = True
    csrf_cookie_samesite: str = 'Lax'
    language_code: str = 'ru'
    time_zone: str = 'UTC'
    use_i18n: bool = True
    use_tz: bool = True

    # Production security settings (can be controlled individually or via use_https)
    use_https: bool = False
    secure_ssl_redirect: bool | None = None
    secure_hsts_seconds: int | None = None
    secure_hsts_include_subdomains: bool | None = None
    secure_hsts_preload: bool | None = None
    session_cookie_secure: bool | None = None
    csrf_cookie_secure: bool | None = None

    secure_browser_xss_filter: bool = True
    secure_content_type_nosniff: bool = True
    x_frame_options: str = 'DENY'

    @property
    def is_secure_ssl_redirect(self) -> bool:
        return self.secure_ssl_redirect if self.secure_ssl_redirect is not None else self.use_https

    @property
    def get_secure_hsts_seconds(self) -> int:
        return self.secure_hsts_seconds if self.secure_hsts_seconds is not None else (31536000 if self.use_https else 0)

    @property
    def is_secure_hsts_include_subdomains(self) -> bool:
        return self.secure_hsts_include_subdomains if self.secure_hsts_include_subdomains is not None else self.use_https

    @property
    def is_secure_hsts_preload(self) -> bool:
        return self.secure_hsts_preload if self.secure_hsts_preload is not None else self.use_https

    @property
    def is_session_cookie_secure(self) -> bool:
        return self.session_cookie_secure if self.session_cookie_secure is not None else self.use_https

    @property
    def is_csrf_cookie_secure(self) -> bool:
        return self.csrf_cookie_secure if self.csrf_cookie_secure is not None else self.use_https

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
