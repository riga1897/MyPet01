#!/bin/bash

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

ENV_TYPE="${1:-}"
if [ -z "$ENV_TYPE" ]; then
    echo "Использование: $0 <preprod|prod>"
    echo "  preprod — настройка препрод VPS (deploy dir: /opt/blog-preprod)"
    echo "  prod    — настройка production VPS (deploy dir: /opt/blog)"
    exit 1
fi

case "$ENV_TYPE" in
    preprod)
        DEPLOY_DIR="/opt/blog-preprod"
        ;;
    prod)
        DEPLOY_DIR="/opt/blog"
        ;;
    *)
        print_error "Неизвестный тип окружения: $ENV_TYPE. Используйте 'preprod' или 'prod'"
        exit 1
        ;;
esac

DEPLOY_USER="${DEPLOY_USER:-depuser}"
ADMIN_USER="${ADMIN_USER:-useradmin}"
SSH_KEY_NAME="github_deploy"
ADMIN_SSH_KEY_NAME="admin_key"

if [ "$(id -u)" -ne 0 ]; then
    print_error "Скрипт должен запускаться от root"
    exit 1
fi

print_header "MyPet01 — Настройка VPS ($ENV_TYPE)"

echo "Параметры:"
echo "  Окружение:                  $ENV_TYPE"
echo "  Директория деплоя:          $DEPLOY_DIR"
echo "  Пользователь деплоя:        $DEPLOY_USER"
echo "  Пользователь администратор: $ADMIN_USER"
echo ""

print_header "1/8 — Обновление системы"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y -o Dpkg::Options::="--force-confold" -o Dpkg::Options::="--force-confdef"
print_success "Система обновлена"

print_header "2/8 — Создание администратора $ADMIN_USER"

if getent passwd "$ADMIN_USER" > /dev/null 2>&1; then
    print_success "Пользователь $ADMIN_USER уже существует"
else
    if id "$ADMIN_USER" &>/dev/null || [ -d "/home/$ADMIN_USER" ]; then
        print_warning "Обнаружены остатки от предыдущего создания $ADMIN_USER. Очищаю..."
        userdel -r "$ADMIN_USER" 2>/dev/null || true
        rm -rf "/home/$ADMIN_USER" 2>/dev/null || true
    fi

    if ! adduser --disabled-password --gecos "" "$ADMIN_USER"; then
        print_error "Не удалось создать пользователя $ADMIN_USER"
        exit 1
    fi
    print_success "Пользователь $ADMIN_USER создан"
fi

if ! getent passwd "$ADMIN_USER" > /dev/null 2>&1; then
    print_error "Пользователь $ADMIN_USER не найден после создания. Проверьте систему."
    exit 1
fi

usermod -aG sudo "$ADMIN_USER"
print_success "$ADMIN_USER добавлен в группу sudo"

ADMIN_SUDOERS_FILE="/etc/sudoers.d/$ADMIN_USER"
echo "$ADMIN_USER ALL=(ALL) NOPASSWD: ALL" > "$ADMIN_SUDOERS_FILE"
if ! chmod 440 "$ADMIN_SUDOERS_FILE"; then
    print_error "Не удалось установить права на sudoers для $ADMIN_USER"
    rm -f "$ADMIN_SUDOERS_FILE"
    exit 1
fi
if ! visudo -cf "$ADMIN_SUDOERS_FILE"; then
    print_error "Ошибка синтаксиса в sudoers для $ADMIN_USER. Удаляю битый файл."
    rm -f "$ADMIN_SUDOERS_FILE"
    exit 1
fi
print_success "Sudo настроен для $ADMIN_USER (полные права, без пароля)"

ADMIN_HOME=$(getent passwd "$ADMIN_USER" | cut -d: -f6)
if [ -z "$ADMIN_HOME" ]; then
    print_error "Не удалось определить домашнюю директорию $ADMIN_USER"
    exit 1
fi
ADMIN_SSH_DIR="$ADMIN_HOME/.ssh"
ADMIN_KEY_PATH="$ADMIN_SSH_DIR/$ADMIN_SSH_KEY_NAME"

if ! mkdir -p "$ADMIN_SSH_DIR"; then
    print_error "Не удалось создать директорию $ADMIN_SSH_DIR"
    exit 1
fi

if [ -f "$ADMIN_KEY_PATH" ]; then
    print_warning "Обнаружены старые SSH ключи $ADMIN_USER — будут перегенерированы!"
    print_warning "Старый приватный ключ станет недействительным!"
fi
rm -f "$ADMIN_KEY_PATH" "$ADMIN_KEY_PATH.pub" "$ADMIN_SSH_DIR/authorized_keys"

if ! ssh-keygen -t ed25519 -C "$ADMIN_USER@$(hostname)" -f "$ADMIN_KEY_PATH" -N ""; then
    print_error "Не удалось сгенерировать SSH ключ для $ADMIN_USER"
    exit 1
fi

cat "$ADMIN_KEY_PATH.pub" > "$ADMIN_SSH_DIR/authorized_keys"
print_success "SSH ключ для $ADMIN_USER сгенерирован и добавлен в authorized_keys"

chown -R "$ADMIN_USER:$ADMIN_USER" "$ADMIN_SSH_DIR"
chmod 700 "$ADMIN_SSH_DIR"
chmod 600 "$ADMIN_SSH_DIR/authorized_keys"
if [ -f "$ADMIN_KEY_PATH" ]; then
    chmod 600 "$ADMIN_KEY_PATH"
    chmod 600 "$ADMIN_KEY_PATH.pub"
fi

print_header "3/8 — Создание пользователя $DEPLOY_USER"

if getent passwd "$DEPLOY_USER" > /dev/null 2>&1; then
    print_success "Пользователь $DEPLOY_USER уже существует"
else
    if id "$DEPLOY_USER" &>/dev/null || [ -d "/home/$DEPLOY_USER" ]; then
        print_warning "Обнаружены остатки от предыдущего создания $DEPLOY_USER. Очищаю..."
        userdel -r "$DEPLOY_USER" 2>/dev/null || true
        rm -rf "/home/$DEPLOY_USER" 2>/dev/null || true
    fi

    if ! adduser --disabled-password --gecos "" "$DEPLOY_USER"; then
        print_error "Не удалось создать пользователя $DEPLOY_USER"
        exit 1
    fi
    print_success "Пользователь $DEPLOY_USER создан"
fi

if ! getent passwd "$DEPLOY_USER" > /dev/null 2>&1; then
    print_error "Пользователь $DEPLOY_USER не найден после создания. Проверьте систему."
    exit 1
fi

SUDOERS_FILE="/etc/sudoers.d/$DEPLOY_USER"
if ! cat > "$SUDOERS_FILE" << 'SUDOERS_EOF'
# Пути /bin/ и /usr/bin/ для совместимости с Ubuntu/Debian

# Установка пакетов (Docker, ufw, fail2ban и др.)
Cmnd_Alias DEPLOY_APT = /usr/bin/apt-get update, /usr/bin/apt-get install *

# Настройка Docker-репозитория
Cmnd_Alias DEPLOY_DOCKER_SETUP = /usr/sbin/usermod -aG docker *, /usr/bin/install -m 0755 -d /etc/apt/keyrings, /usr/bin/gpg --dearmor -o /etc/apt/keyrings/docker.gpg, /bin/chmod a+r /etc/apt/keyrings/docker.gpg, /usr/bin/chmod a+r /etc/apt/keyrings/docker.gpg, /usr/bin/tee /etc/apt/sources.list.d/docker.list

# Создание директорий деплоя
Cmnd_Alias DEPLOY_DIRS = /bin/mkdir -p *, /usr/bin/mkdir -p *, /bin/chown -R *, /usr/bin/chown -R *

# Управление сервисами (docker, ufw, fail2ban)
Cmnd_Alias DEPLOY_SYSTEMCTL = /usr/bin/systemctl enable docker, /usr/bin/systemctl start docker, /usr/bin/systemctl restart docker, /usr/bin/systemctl enable fail2ban, /usr/bin/systemctl start fail2ban, /usr/bin/systemctl restart fail2ban

# Настройка файрвола
Cmnd_Alias DEPLOY_UFW = /usr/sbin/ufw default *, /usr/sbin/ufw allow *, /usr/sbin/ufw enable, /usr/sbin/ufw status *

# Настройка sysctl (net.ipv4.ip_unprivileged_port_start для HAProxy)
Cmnd_Alias DEPLOY_SYSCTL = /usr/sbin/sysctl -p, /usr/bin/tee -a /etc/sysctl.conf
SUDOERS_EOF
then
    print_error "Не удалось создать файл sudoers"
    exit 1
fi
echo "$DEPLOY_USER ALL=(ALL) NOPASSWD: DEPLOY_APT, DEPLOY_DOCKER_SETUP, DEPLOY_DIRS, DEPLOY_SYSTEMCTL, DEPLOY_UFW, DEPLOY_SYSCTL" >> "$SUDOERS_FILE"
if ! chmod 440 "$SUDOERS_FILE"; then
    print_error "Не удалось установить права на sudoers"
    rm -f "$SUDOERS_FILE"
    exit 1
fi
if ! visudo -cf "$SUDOERS_FILE"; then
    print_error "Ошибка синтаксиса в sudoers. Удаляю битый файл."
    rm -f "$SUDOERS_FILE"
    exit 1
fi
print_success "Sudo настроен для $DEPLOY_USER (ограниченные права)"

print_header "4/8 — SSH ключ для GitHub Actions"

DEPLOY_HOME=$(getent passwd "$DEPLOY_USER" | cut -d: -f6)
if [ -z "$DEPLOY_HOME" ]; then
    print_error "Не удалось определить домашнюю директорию $DEPLOY_USER"
    exit 1
fi
SSH_DIR="$DEPLOY_HOME/.ssh"
KEY_PATH="$SSH_DIR/$SSH_KEY_NAME"

if ! mkdir -p "$SSH_DIR"; then
    print_error "Не удалось создать директорию $SSH_DIR"
    exit 1
fi

if [ -f "$KEY_PATH" ]; then
    print_warning "Обнаружены старые SSH ключи $DEPLOY_USER — будут перегенерированы!"
    print_warning "Старый приватный ключ станет недействительным! Обновите GitHub Secret."
fi
rm -f "$KEY_PATH" "$KEY_PATH.pub" "$SSH_DIR/authorized_keys"

if ! ssh-keygen -t ed25519 -C "github-actions-deploy" -f "$KEY_PATH" -N ""; then
    print_error "Не удалось сгенерировать SSH ключ"
    exit 1
fi

cat "$KEY_PATH.pub" > "$SSH_DIR/authorized_keys"
print_success "SSH ключ $DEPLOY_USER сгенерирован и добавлен в authorized_keys"

if ! getent passwd "$DEPLOY_USER" > /dev/null 2>&1; then
    print_error "Пользователь $DEPLOY_USER не найден перед chown. Невозможно установить владельца."
    exit 1
fi
if ! chown -R "$DEPLOY_USER:$DEPLOY_USER" "$SSH_DIR"; then
    print_error "Не удалось установить владельца $SSH_DIR"
    exit 1
fi
chmod 700 "$SSH_DIR"
chmod 600 "$SSH_DIR/authorized_keys"
if [ -f "$KEY_PATH" ]; then
    chmod 600 "$KEY_PATH"
    chmod 600 "$KEY_PATH.pub"
fi

print_header "5/8 — Блокировка ICMP (ping)"

SYSCTL_CONF="/etc/sysctl.conf"
if grep -q "net.ipv4.icmp_echo_ignore_all" "$SYSCTL_CONF"; then
    sed -i 's/^.*net.ipv4.icmp_echo_ignore_all.*/net.ipv4.icmp_echo_ignore_all = 1/' "$SYSCTL_CONF"
else
    echo "net.ipv4.icmp_echo_ignore_all = 1" >> "$SYSCTL_CONF"
fi
sysctl -p > /dev/null 2>&1
print_success "ICMP (ping) заблокирован — сервер не отвечает на ping"

print_header "6/8 — Отключение root SSH"

SSHD_CONFIG="/etc/ssh/sshd_config"
if [ -f "$SSHD_CONFIG" ]; then
    if grep -q "^PermitRootLogin" "$SSHD_CONFIG"; then
        sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' "$SSHD_CONFIG"
    elif grep -q "^#PermitRootLogin" "$SSHD_CONFIG"; then
        sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' "$SSHD_CONFIG"
    else
        echo "PermitRootLogin no" >> "$SSHD_CONFIG"
    fi
    print_success "PermitRootLogin no установлен в $SSHD_CONFIG"

    if systemctl restart sshd 2>/dev/null || systemctl restart ssh 2>/dev/null; then
        print_success "SSH сервис перезапущен"
    else
        print_warning "Не удалось перезапустить SSH. Перезапустите вручную: systemctl restart sshd"
    fi
else
    print_warning "Файл $SSHD_CONFIG не найден. Настройте PermitRootLogin вручную."
fi

print_header "7/8 — Настройка GeoIP (обновление списка российских IP)"

GEOIP_SCRIPT="${DEPLOY_DIR}/haproxy/update-geoip.sh"
GEOIP_LOG="/var/log/update-geoip.log"
CRON_SCHEDULE="0 4 * * 0"

touch "$GEOIP_LOG"
chown "$DEPLOY_USER:$DEPLOY_USER" "$GEOIP_LOG"

CRON_CMD="${CRON_SCHEDULE} test -f ${GEOIP_SCRIPT} && ${GEOIP_SCRIPT} >> ${GEOIP_LOG} 2>&1"
EXISTING_CRON=$(crontab -u "$DEPLOY_USER" -l 2>/dev/null || true)

if echo "$EXISTING_CRON" | grep -qF "update-geoip.sh"; then
    print_warning "Cron для update-geoip.sh уже настроен — обновляю"
    NEW_CRON=$(echo "$EXISTING_CRON" | grep -vF "update-geoip.sh")
    echo "${NEW_CRON}
${CRON_CMD}" | crontab -u "$DEPLOY_USER" -
else
    echo "${EXISTING_CRON}
${CRON_CMD}" | crontab -u "$DEPLOY_USER" -
fi
print_success "Cron настроен: обновление GeoIP каждое воскресенье в 04:00"
print_success "Лог: ${GEOIP_LOG}"

mkdir -p "${DEPLOY_DIR}/haproxy/geoip"
chown "$DEPLOY_USER:$DEPLOY_USER" "${DEPLOY_DIR}"
chown "$DEPLOY_USER:$DEPLOY_USER" "${DEPLOY_DIR}/haproxy"
chown "$DEPLOY_USER:$DEPLOY_USER" "${DEPLOY_DIR}/haproxy/geoip"
print_success "Директория ${DEPLOY_DIR}/haproxy/geoip создана, владелец: ${DEPLOY_USER}"

if [ -f "${GEOIP_SCRIPT}" ]; then
    print_warning "Запуск первичного обновления GeoIP..."
    if sudo -u "$DEPLOY_USER" bash "${GEOIP_SCRIPT}"; then
        NETWORK_COUNT=$(wc -l < "${DEPLOY_DIR}/haproxy/geoip/ru_networks.lst" 2>/dev/null || echo "0")
        print_success "GeoIP обновлён: ${NETWORK_COUNT} сетей"
    else
        print_warning "Первичное обновление GeoIP не удалось"
        print_warning "GeoIP обновится по cron после деплоя"
    fi
else
    print_warning "Скрипт ${GEOIP_SCRIPT} ещё не существует (появится после первого деплоя)"
    print_warning "Cron запустит обновление GeoIP автоматически после деплоя"
fi

print_header "8/8 — Настройка автобана (блокировка агрессивных IP)"

AUTOBAN_SCRIPT="${DEPLOY_DIR}/haproxy/auto-ban.sh"
AUTOBAN_LOG="/var/log/haproxy-autoban.log"
AUTOBAN_CRON_SCHEDULE="*/15 * * * *"

touch "$AUTOBAN_LOG"
chown "$DEPLOY_USER:$DEPLOY_USER" "$AUTOBAN_LOG"

AUTOBAN_CRON_CMD="${AUTOBAN_CRON_SCHEDULE} test -f ${AUTOBAN_SCRIPT} && ${AUTOBAN_SCRIPT} >> ${AUTOBAN_LOG} 2>&1"
EXISTING_CRON=$(crontab -u "$DEPLOY_USER" -l 2>/dev/null || true)

if echo "$EXISTING_CRON" | grep -qF "auto-ban.sh"; then
    print_warning "Cron для auto-ban.sh уже настроен — обновляю"
    NEW_CRON=$(echo "$EXISTING_CRON" | grep -vF "auto-ban.sh")
    echo "${NEW_CRON}
${AUTOBAN_CRON_CMD}" | crontab -u "$DEPLOY_USER" -
else
    echo "${EXISTING_CRON}
${AUTOBAN_CRON_CMD}" | crontab -u "$DEPLOY_USER" -
fi
print_success "Cron настроен: автобан каждые 15 минут"
print_success "Лог: ${AUTOBAN_LOG}"

mkdir -p "${DEPLOY_DIR}/haproxy/blacklist"
chown "$DEPLOY_USER:$DEPLOY_USER" "${DEPLOY_DIR}/haproxy/blacklist"
print_success "Директория ${DEPLOY_DIR}/haproxy/blacklist создана"

echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  ВАЖНО: Скопируйте приватные ключи!                     ║${NC}"
echo -e "${YELLOW}║                                                          ║${NC}"
echo -e "${YELLOW}║  1. Ключ $ADMIN_USER — для подключения к серверу по SSH   ║${NC}"
echo -e "${YELLOW}║  2. Ключ $DEPLOY_USER — в GitHub Secret для CI/CD        ║${NC}"
echo -e "${YELLOW}║     Secret name: PREPROD_SSH_KEY (или SSH_KEY для prod)   ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}=== SSH ключ администратора ($ADMIN_USER) ===${NC}"
echo -e "${GREEN}--- НАЧАЛО КЛЮЧА $ADMIN_USER ---${NC}"
cat "$ADMIN_KEY_PATH"
echo -e "${GREEN}--- КОНЕЦ КЛЮЧА $ADMIN_USER ---${NC}"
echo ""

echo -e "${BLUE}=== SSH ключ деплоя ($DEPLOY_USER) ===${NC}"
echo -e "${GREEN}--- НАЧАЛО КЛЮЧА $DEPLOY_USER ---${NC}"
cat "$KEY_PATH"
echo -e "${GREEN}--- КОНЕЦ КЛЮЧА $DEPLOY_USER ---${NC}"
echo ""

print_header "Настройка завершена!"

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo -e "${GREEN}VPS готов к деплою!${NC}"
echo ""
echo "Информация для подключения к серверу:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  IP сервера:          ${YELLOW}$SERVER_IP${NC}"
echo -e "  Администратор:       ${YELLOW}$ADMIN_USER${NC} (sudo без пароля)"
echo -e "  Подключение:         ${YELLOW}ssh -i admin_key $ADMIN_USER@$SERVER_IP${NC}"
echo -e "  Root SSH:            ${RED}ОТКЛЮЧЁН${NC}"
echo ""
echo "Информация для GitHub Secrets:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$ENV_TYPE" = "preprod" ]; then
    echo -e "  PREPROD_SERVER_IP:   ${YELLOW}$SERVER_IP${NC}"
    echo -e "  PREPROD_SSH_USER:    ${YELLOW}$DEPLOY_USER${NC}"
    echo -e "  PREPROD_DEPLOY_DIR:  ${YELLOW}$DEPLOY_DIR${NC}"
    echo -e "  PREPROD_SSH_KEY:     ${YELLOW}(приватный ключ $DEPLOY_USER выше)${NC}"
else
    echo -e "  SERVER_IP:           ${YELLOW}$SERVER_IP${NC}"
    echo -e "  SSH_USER:            ${YELLOW}$DEPLOY_USER${NC}"
    echo -e "  DEPLOY_DIR:          ${YELLOW}$DEPLOY_DIR${NC}"
    echo -e "  SSH_KEY:             ${YELLOW}(приватный ключ $DEPLOY_USER выше)${NC}"
fi
echo ""
echo -e "${BLUE}При первом деплое CI/CD автоматически установит:${NC}"
echo -e "${BLUE}  - Docker CE и Docker Compose${NC}"
echo -e "${BLUE}  - UFW (файрвол)${NC}"
echo -e "${BLUE}  - Fail2ban (защита от брутфорса)${NC}"
echo -e "${BLUE}  - Создаст директорию деплоя${NC}"
echo ""
echo "Следующий шаг:"
echo "  1. Скопируйте ключ $ADMIN_USER — для подключения к серверу"
echo "  2. Скопируйте ключ $DEPLOY_USER в GitHub Secret"
echo "  3. Добавьте остальные секреты (см. docs/DEPLOY_CHECKLIST.md)"
echo "  4. Сделайте git push в release/* ветку"
echo "  5. Всё остальное CI/CD сделает автоматически"
echo ""
