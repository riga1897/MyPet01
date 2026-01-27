#!/bin/bash
set -e

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    echo "INFO: .env file already exists. Skipping generation (idempotent)."
    echo "To regenerate, delete .env and run this script again."
    exit 0
fi

echo "Generating pre-production .env file..."

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
# Pre-Production Environment
# Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
# Server: $SERVER_IP

# Django
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$SERVER_IP,localhost,127.0.0.1

# Database
POSTGRES_DB=blog_db
POSTGRES_USER=blog_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://blog_user:$POSTGRES_PASSWORD@db:5432/blog_db

# Redis
REDIS_URL=redis://redis:6379/0

# Security
CSRF_TRUSTED_ORIGINS=http://$SERVER_IP,https://$SERVER_IP
SECURE_SSL_REDIRECT=False
EOF

chmod 600 "$ENV_FILE"

echo "Pre-production .env file created successfully!"
echo "Server IP: $SERVER_IP"
