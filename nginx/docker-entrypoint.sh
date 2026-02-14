#!/bin/sh
set -e

DOMAIN="www.mine-craft.su"
CERT_DIR="/etc/letsencrypt/live/$DOMAIN"
ARCHIVE_DIR="/etc/letsencrypt/archive/$DOMAIN"
TEMP_CERT_DIR="/etc/nginx/ssl-temp"
DH_PARAMS="/etc/letsencrypt/ssl-dhparams.pem"
BUNDLED_DH="/etc/nginx/ssl-dhparams.pem"

has_real_cert_in_archive() {
    [ -f "$ARCHIVE_DIR/fullchain1.pem" ] && [ -f "$ARCHIVE_DIR/privkey1.pem" ]
}

if has_real_cert_in_archive; then
    echo "[entrypoint] Real SSL certificate found in archive. Linking..."
    rm -rf "$CERT_DIR"
    mkdir -p "$CERT_DIR"
    LATEST_NUM=$(ls "$ARCHIVE_DIR"/fullchain*.pem 2>/dev/null | sed 's/.*fullchain\([0-9]*\)\.pem/\1/' | sort -n | tail -1)
    ln -sf "$ARCHIVE_DIR/fullchain${LATEST_NUM}.pem" "$CERT_DIR/fullchain.pem"
    ln -sf "$ARCHIVE_DIR/privkey${LATEST_NUM}.pem" "$CERT_DIR/privkey.pem"
    ln -sf "$ARCHIVE_DIR/chain${LATEST_NUM}.pem" "$CERT_DIR/chain.pem"
    ln -sf "$ARCHIVE_DIR/cert${LATEST_NUM}.pem" "$CERT_DIR/cert.pem"
    echo "[entrypoint] SSL certificate linked from archive (version ${LATEST_NUM})."
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
fi

if [ ! -f "$DH_PARAMS" ]; then
    echo "[entrypoint] DH params not found. Copying bundled params..."
    cp "$BUNDLED_DH" "$DH_PARAMS"
    echo "[entrypoint] DH params ready."
fi

exec /docker-entrypoint.sh nginx -g "daemon off;"
