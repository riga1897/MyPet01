from pathlib import Path
import dj_database_url
from mypet_project.config import settings as env_settings

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = env_settings.debug
SECRET_KEY = env_settings.secret_key
ALLOWED_HOSTS = env_settings.allowed_hosts_list

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
    'blog',
    'users',
]

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.BrowserCacheMiddleware',
]

ROOT_URLCONF = 'mypet_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mypet_project.wsgi.application'

DATABASE_URL = env_settings.get_database_url()
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL) if DATABASE_URL else {}
}

CSRF_TRUSTED_ORIGINS = env_settings.csrf_trusted_origins_list
CSRF_COOKIE_SECURE = env_settings.csrf_cookie_secure
CSRF_COOKIE_HTTPONLY = env_settings.csrf_cookie_httponly
CSRF_COOKIE_SAMESITE = env_settings.csrf_cookie_samesite

LANGUAGE_CODE = env_settings.language_code
TIME_ZONE = env_settings.time_zone
USE_I18N = env_settings.use_i18n
USE_TZ = env_settings.use_tz

# Production security settings
SECURE_SSL_REDIRECT = env_settings.is_secure_ssl_redirect
SECURE_HSTS_SECONDS = env_settings.get_secure_hsts_seconds
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_settings.is_secure_hsts_include_subdomains
SECURE_HSTS_PRELOAD = env_settings.is_secure_hsts_preload
SESSION_COOKIE_SECURE = env_settings.is_session_cookie_secure
CSRF_COOKIE_SECURE = env_settings.is_csrf_cookie_secure
SECURE_BROWSER_XSS_FILTER = env_settings.secure_browser_xss_filter
SECURE_CONTENT_TYPE_NOSNIFF = env_settings.secure_content_type_nosniff
X_FRAME_OPTIONS = env_settings.x_frame_options

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache configuration
CACHE_BACKENDS_MAP = {
    'locmem': 'django.core.cache.backends.locmem.LocMemCache',
    'db': 'django.core.cache.backends.db.DatabaseCache',
    'redis': 'django.core.cache.backends.redis.RedisCache',
    'memcached': 'django.core.cache.backends.memcached.PyMemcacheCache',
}

CACHES = {
    'default': {
        'BACKEND': CACHE_BACKENDS_MAP.get(
            env_settings.cache_backend,
            'django.core.cache.backends.locmem.LocMemCache'
        ),
        'LOCATION': env_settings.cache_location,
        'TIMEOUT': env_settings.cache_timeout,
    }
}
