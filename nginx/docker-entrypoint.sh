#!/bin/sh
set -e

DOMAIN="www.mine-craft.su"
CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
TEMP_CERT_DIR="/etc/nginx/ssl-temp"
DH_PARAMS="/etc/letsencrypt/ssl-dhparams.pem"
BUNDLED_DH="/etc/nginx/ssl-dhparams.pem"

is_real_cert() {
    [ -f "$CERT_DIR/fullchain.pem" ] && [ ! -L "$CERT_DIR/fullchain.pem" ]
}

if is_real_cert; then
    echo "[entrypoint] Real SSL certificate found. Using it."
else
    echo "[entrypoint] No real SSL certificate. Creating temporary self-signed..."

    if ! command -v openssl > /dev/null 2>&1; then
        apk add --no-cache openssl > /dev/null 2>&1
    fi

    mkdir -p "$TEMP_CERT_DIR"
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout "$TEMP_CERT_DIR/privkey.pem" \
        -out "$TEMP_CERT_DIR/fullchain.pem" \
        -subj "/CN=$DOMAIN/O=Temporary" 2>/dev/null

    rm -rf "$CERT_DIR"
    mkdir -p "$CERT_DIR"
    ln -sf "$TEMP_CERT_DIR/fullchain.pem" "$CERT_DIR/fullchain.pem"
    ln -sf "$TEMP_CERT_DIR/privkey.pem" "$CERT_DIR/privkey.pem"

    echo "[entrypoint] Temporary self-signed certificate linked to $CERT_DIR"
    echo "[entrypoint] Run 'init-ssl.sh' to obtain a real Let's Encrypt certificate."
fi

if [ ! -f "$DH_PARAMS" ]; then
    echo "[entrypoint] DH params not found. Copying bundled params..."
    cp "$BUNDLED_DH" "$DH_PARAMS"
    echo "[entrypoint] DH params ready."
fi

exec /docker-entrypoint.sh nginx -g "daemon off;"
