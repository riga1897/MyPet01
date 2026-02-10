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

DEPLOY_USER="${DEPLOY_USER:-depuser}"
SSH_KEY_NAME="github_deploy"

if [ "$(id -u)" -ne 0 ]; then
    print_error "Скрипт должен запускаться от root"
    exit 1
fi

print_header "MyPet01 — Настройка VPS"

echo "Параметры:"
echo "  Пользователь: $DEPLOY_USER"
echo ""

print_header "1/2 — Создание пользователя $DEPLOY_USER"

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
SUDOERS_EOF
then
    print_error "Не удалось создать файл sudoers"
    exit 1
fi
echo "$DEPLOY_USER ALL=(ALL) NOPASSWD: DEPLOY_APT, DEPLOY_DOCKER_SETUP, DEPLOY_DIRS, DEPLOY_SYSTEMCTL, DEPLOY_UFW" >> "$SUDOERS_FILE"
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

print_header "2/2 — SSH ключ для GitHub Actions"

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

KEY_EXISTED=false
if [ -f "$KEY_PATH" ]; then
    print_warning "SSH ключ уже существует: $KEY_PATH"
    KEY_EXISTED=true
else
    if ! ssh-keygen -t ed25519 -C "github-actions-deploy" -f "$KEY_PATH" -N ""; then
        print_error "Не удалось сгенерировать SSH ключ"
        exit 1
    fi

    touch "$SSH_DIR/authorized_keys"
    cat "$KEY_PATH.pub" >> "$SSH_DIR/authorized_keys"
    sort -u "$SSH_DIR/authorized_keys" -o "$SSH_DIR/authorized_keys"

    print_success "SSH ключ сгенерирован"
fi

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

echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  ВАЖНО: Скопируйте приватный ключ в GitHub Secret    ║${NC}"
echo -e "${YELLOW}║  Secret name: PREPROD_SSH_KEY (или SSH_KEY для prod)  ║${NC}"
echo -e "${YELLOW}║  SSH_USER: $DEPLOY_USER                               ║${NC}"
echo -e "${YELLOW}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
if [ "$KEY_EXISTED" = true ]; then
    print_warning "Ключ был создан ранее. Если нужно показать его снова:"
    echo "  cat $KEY_PATH"
else
    echo -e "${GREEN}--- НАЧАЛО КЛЮЧА (скопируйте всё включая BEGIN и END) ---${NC}"
    cat "$KEY_PATH"
    echo -e "${GREEN}--- КОНЕЦ КЛЮЧА ---${NC}"
fi
echo ""

print_header "Настройка завершена!"

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo -e "${GREEN}VPS готов к деплою!${NC}"
echo ""
echo "Информация для GitHub Secrets:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  PREPROD_SERVER_IP:   ${YELLOW}$SERVER_IP${NC}"
echo -e "  PREPROD_SSH_USER:    ${YELLOW}$DEPLOY_USER${NC}"
echo -e "  PREPROD_DEPLOY_DIR:  ${YELLOW}/opt/blog-preprod${NC}"
echo -e "  PREPROD_SSH_KEY:     ${YELLOW}(приватный ключ выше)${NC}"
echo ""
echo -e "${BLUE}При первом деплое CI/CD автоматически установит:${NC}"
echo -e "${BLUE}  - Docker CE и Docker Compose${NC}"
echo -e "${BLUE}  - UFW (файрвол)${NC}"
echo -e "${BLUE}  - Fail2ban (защита от брутфорса)${NC}"
echo -e "${BLUE}  - Создаст директорию деплоя${NC}"
echo ""
echo "Следующий шаг:"
echo "  1. Скопируйте приватный ключ в GitHub Secret"
echo "  2. Добавьте остальные секреты (см. docs/DEPLOY_CHECKLIST.md)"
echo "  3. Сделайте git push в release/* ветку"
echo "  4. Всё остальное CI/CD сделает автоматически"
echo ""
