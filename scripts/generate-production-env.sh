#!/bin/bash
set -e

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    echo "INFO: .env file already exists. Skipping generation (idempotent)."
    echo "To regenerate, delete .env and run this script again."
    exit 0
fi

echo "Generating production .env file..."

if [ -z "$SERVER_IP" ]; then
    echo "ERROR: SERVER_IP environment variable is not set!"
    exit 1
fi

generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(50).replace('\$', 'X'))"
}

generate_password() {
    openssl rand -base64 24 | tr -d '/+=' | head -c 24
}

SECRET_KEY=$(generate_secret_key)
POSTGRES_PASSWORD=$(generate_password)

cat > "$ENV_FILE" << EOF
# ========================================
# НАСТРОЙКИ ПРИЛОЖЕНИЯ (Production)
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# Server: $SERVER_IP
# ========================================

# Основные настройки
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$SERVER_IP,www.mine-craft.su,site.mine-craft.su,localhost,127.0.0.1

# База данных
DATABASE_URL=postgresql://blog_user:$POSTGRES_PASSWORD@db:5432/blog_db
POSTGRES_DB=blog_db
POSTGRES_USER=blog_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=db
POSTGRES_PORT=5432

# CSRF
CSRF_TRUSTED_ORIGINS=https://www.mine-craft.su,https://site.mine-craft.su
CSRF_COOKIE_HTTPONLY=True
CSRF_COOKIE_SAMESITE=Lax

# Безопасность (включить после настройки SSL)
USE_HTTPS=False

# Локализация
LANGUAGE_CODE=ru
TIME_ZONE=UTC
USE_I18N=True
USE_TZ=True

# URL-адреса
STATIC_URL=/static/
MEDIA_URL=/media/
LOGIN_URL=/users/login/
LOGIN_REDIRECT_URL=/
LOGOUT_REDIRECT_URL=/

# Кэш (сервер) - Redis
CACHE_BACKEND=redis
CACHE_LOCATION=redis://redis:6379/0
CACHE_TIMEOUT=300

# Кэш (браузер)
BROWSER_CACHE_ENABLED=True
BROWSER_CACHE_MAX_AGE=86400

# Админка
ADMIN_SHOW_FACETS=True

# Redis
REDIS_URL=redis://redis:6379/0
EOF

chmod 600 "$ENV_FILE"

echo "Production .env file created successfully!"
echo "Server IP: $SERVER_IP"
echo "Domains: www.mine-craft.su, site.mine-craft.su"
