#!/bin/sh
set -e

CERT_DIR="/etc/letsencrypt/live/www.mine-craft.su"
DH_PARAMS="/etc/letsencrypt/ssl-dhparams.pem"
BUNDLED_DH="/etc/nginx/ssl-dhparams.pem"

if [ ! -f "$CERT_DIR/fullchain.pem" ] || [ ! -f "$CERT_DIR/privkey.pem" ]; then
    echo "[entrypoint] SSL certificate not found. Creating self-signed certificate..."

    if ! command -v openssl > /dev/null 2>&1; then
        apk add --no-cache openssl > /dev/null 2>&1
    fi

    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout "$CERT_DIR/privkey.pem" \
        -out "$CERT_DIR/fullchain.pem" \
        -subj "/CN=localhost/O=Dummy"
    echo "[entrypoint] Self-signed certificate created."
fi

if [ ! -f "$DH_PARAMS" ]; then
    echo "[entrypoint] DH params not found. Copying bundled params..."
    cp "$BUNDLED_DH" "$DH_PARAMS"
    echo "[entrypoint] DH params ready."
fi

exec /docker-entrypoint.sh nginx -g "daemon off;"
