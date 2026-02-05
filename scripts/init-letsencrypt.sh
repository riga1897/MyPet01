#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[OK] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

DOMAINS="${DOMAINS:-www.mine-craft.su site.mine-craft.su}"
EMAIL="${EMAIL:-admin@mine-craft.su}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
STAGING="${STAGING:-0}"

CERT_NAME=$(echo "$DOMAINS" | awk '{print $1}')

print_header "Let's Encrypt — Инициализация сертификатов"

echo "Параметры:"
echo "  Домены:     $DOMAINS"
echo "  Email:      $EMAIL"
echo "  Compose:    $COMPOSE_FILE"
echo "  Staging:    $STAGING (1 = тестовый режим)"
echo "  Cert name:  $CERT_NAME"
echo ""

if [ "$STAGING" = "1" ]; then
    print_warning "STAGING режим: будет выдан тестовый сертификат (не доверенный браузерами)"
fi

read -p "Продолжить? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Отменено."
    exit 0
fi

print_header "1/5 — Скачивание параметров Diffie-Hellman"

docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "" certbot sh -c "
    if [ ! -f /etc/letsencrypt/ssl-dhparams.pem ]; then
        echo 'Downloading ssl-dhparams.pem...'
        wget -q -O /etc/letsencrypt/ssl-dhparams.pem https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem
        echo 'Done.'
    else
        echo 'ssl-dhparams.pem already exists.'
    fi
"

print_success "TLS параметры загружены"

print_header "2/5 — Создание временного самоподписанного сертификата"

CERT_DIR="/etc/letsencrypt/live/$CERT_NAME"

docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "" certbot sh -c "
    if [ -d '$CERT_DIR' ] && [ -f '$CERT_DIR/fullchain.pem' ]; then
        echo 'Certificate already exists. Checking if it is a dummy...'
        if openssl x509 -in '$CERT_DIR/fullchain.pem' -noout -issuer 2>/dev/null | grep -q 'O=Dummy'; then
            echo 'Dummy certificate found, will be replaced.'
        else
            echo 'Real certificate found. Skipping dummy creation.'
            echo 'REAL_CERT_EXISTS=true'
            exit 0
        fi
    fi

    echo 'Creating dummy certificate for nginx startup...'
    mkdir -p '$CERT_DIR'
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout '$CERT_DIR/privkey.pem' \
        -out '$CERT_DIR/fullchain.pem' \
        -subj '/CN=localhost/O=Dummy'
    echo 'Dummy certificate created.'
"

REAL_EXISTS=$(docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "" certbot sh -c "
    if [ -f '$CERT_DIR/fullchain.pem' ] && openssl x509 -in '$CERT_DIR/fullchain.pem' -noout -issuer 2>/dev/null | grep -qv 'O=Dummy'; then
        echo 'true'
    else
        echo 'false'
    fi
" 2>/dev/null | tail -1)

if [ "$REAL_EXISTS" = "true" ]; then
    print_warning "Настоящий сертификат уже установлен. Пропускаем получение нового."
    print_header "Готово!"
    echo -e "${GREEN}Сертификаты уже настроены. Перезапустите стек:${NC}"
    echo "  docker compose -f $COMPOSE_FILE restart nginx"
    exit 0
fi

print_success "Временный сертификат создан"

print_header "3/5 — Запуск nginx с временным сертификатом"

docker compose -f "$COMPOSE_FILE" up -d nginx haproxy
sleep 5

if docker compose -f "$COMPOSE_FILE" ps nginx | grep -q "running"; then
    print_success "Nginx запущен"
else
    print_error "Nginx не запустился!"
    docker compose -f "$COMPOSE_FILE" logs nginx --tail=20
    exit 1
fi

print_header "4/5 — Получение сертификата Let's Encrypt"

DOMAIN_ARGS=""
for domain in $DOMAINS; do
    DOMAIN_ARGS="$DOMAIN_ARGS -d $domain"
done

STAGING_ARG=""
if [ "$STAGING" = "1" ]; then
    STAGING_ARG="--staging"
fi

docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "" certbot sh -c "
    rm -rf /etc/letsencrypt/live/$CERT_NAME
    rm -rf /etc/letsencrypt/archive/$CERT_NAME
    rm -rf /etc/letsencrypt/renewal/$CERT_NAME.conf
"

docker compose -f "$COMPOSE_FILE" run --rm certbot certonly \
    --webroot \
    -w /var/www/certbot \
    $DOMAIN_ARGS \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    $STAGING_ARG

print_success "Сертификат получен!"

print_header "5/5 — Копирование сертификатов и перезагрузка сервисов"

mkdir -p nginx/ssl
docker compose -f "$COMPOSE_FILE" run --rm --entrypoint "" certbot sh -c "
    cp /etc/letsencrypt/live/$CERT_NAME/fullchain.pem /ssl-copy/fullchain.pem
    cp /etc/letsencrypt/live/$CERT_NAME/privkey.pem /ssl-copy/privkey.pem
"
print_success "Сертификаты скопированы для VPN (nginx/ssl/)"

docker compose -f "$COMPOSE_FILE" exec nginx nginx -s reload
print_success "Nginx перезагружен с новым сертификатом"

docker compose -f "$COMPOSE_FILE" up -d certbot
print_success "Certbot запущен для автообновления (проверка каждые 12 часов)"

CRON_CMD="0 0 * * 0 cd $(pwd) && docker compose -f $COMPOSE_FILE exec -T nginx nginx -s reload > /dev/null 2>&1"
if ! crontab -l 2>/dev/null | grep -qF "nginx -s reload"; then
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    print_success "Cron задача добавлена: перезагрузка nginx каждое воскресенье"
else
    print_warning "Cron задача уже существует"
fi

print_header "Готово!"

echo -e "${GREEN}SSL сертификаты Let's Encrypt установлены и настроены!${NC}"
echo ""
echo "Домены:         $DOMAINS"
echo "Автообновление: каждые 12 часов (certbot контейнер)"
echo "Reload nginx:   каждое воскресенье (cron)"
echo "Срок действия:  90 дней (обновляется автоматически за 30 дней)"
echo ""
echo "Полезные команды:"
echo "  docker compose -f $COMPOSE_FILE exec certbot certbot certificates"
echo "  docker compose -f $COMPOSE_FILE exec nginx nginx -s reload"
echo "  docker compose -f $COMPOSE_FILE logs certbot"
echo ""
