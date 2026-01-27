#!/bin/bash
set -e

BLOG_DIR="/opt/blog"
SSL_DIR="${BLOG_DIR}/nginx/ssl"

echo "$(date): Starting certificate renewal..."

certbot renew --quiet --deploy-hook "
    echo 'Copying renewed certificates...'
    cp /etc/letsencrypt/live/mine-craft.su/fullchain.pem ${SSL_DIR}/fullchain.pem
    cp /etc/letsencrypt/live/mine-craft.su/privkey.pem ${SSL_DIR}/privkey.pem
    chmod 644 ${SSL_DIR}/fullchain.pem
    chmod 600 ${SSL_DIR}/privkey.pem
    
    echo 'Restarting services...'
    cd ${BLOG_DIR}
    docker compose -f docker-compose.prod.yml restart nginx
    docker compose -f docker-compose.prod.yml restart softether
    
    echo 'Certificate renewal completed!'
"

echo "$(date): Renewal check finished."
