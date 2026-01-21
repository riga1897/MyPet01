import os
import environ
from pathlib import Path

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False)
)

BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Django Settings
DEBUG = env('DEBUG', cast=bool, default=False)  # type: ignore
SECRET_KEY = env('SECRET_KEY', cast=str, default='django-insecure-dummy-key')  # type: ignore
ALLOWED_HOSTS = env('ALLOWED_HOSTS', cast=list, default=['*'])  # type: ignore

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'blog',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mypet_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# Database
# If DATABASE_URL is not set, construct it from individual POSTGRES_* variables
DATABASE_URL = env('DATABASE_URL', cast=str, default='')  # type: ignore
if not DATABASE_URL:
    try:
        POSTGRES_USER = env('POSTGRES_USER', cast=str)  # type: ignore
        POSTGRES_PASSWORD = env('POSTGRES_PASSWORD', cast=str)  # type: ignore
        POSTGRES_HOST = env('POSTGRES_HOST', cast=str)  # type: ignore
        POSTGRES_PORT = env('POSTGRES_PORT', cast=str)  # type: ignore
        POSTGRES_DB = env('POSTGRES_DB', cast=str)  # type: ignore
        DATABASE_URL = f"postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    except Exception:
        # Fallback to empty if variables are missing
        DATABASE_URL = ''

DATABASES = {
    'default': env.db_url('DATABASE_URL', default=DATABASE_URL)  # type: ignore
}

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS', cast=list, default=[  # type: ignore
    'https://*.replit.dev',
    'https://*.repl.co',
    'https://*.pike.replit.dev'
])

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

