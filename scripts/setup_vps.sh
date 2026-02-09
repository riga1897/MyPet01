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

DEPLOY_DIR="${DEPLOY_DIR:-/opt/blog-preprod}"
DEPLOY_USER="${DEPLOY_USER:-depuser}"
SSH_KEY_NAME="github_deploy"

print_header "MyPet01 — Настройка VPS"

echo "Параметры:"
echo "  Директория деплоя: $DEPLOY_DIR"
echo "  Пользователь:      $DEPLOY_USER"
echo ""
read -p "Продолжить? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Отменено."
    exit 0
fi

print_header "1/5 — Обновление системы"

apt-get update
apt-get upgrade -y
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    htop \
    git

print_success "Система обновлена"

print_header "2/5 — Создание пользователя $DEPLOY_USER"

if id "$DEPLOY_USER" &>/dev/null; then
    print_warning "Пользователь $DEPLOY_USER уже существует"
else
    adduser --disabled-password --gecos "" "$DEPLOY_USER"
    print_success "Пользователь $DEPLOY_USER создан"
fi

SUDOERS_FILE="/etc/sudoers.d/$DEPLOY_USER"
cat > "$SUDOERS_FILE" << 'SUDOERS_EOF'
# Команды для первоначальной установки Docker (CI/CD)
# Пути /bin/ и /usr/bin/ для совместимости с Ubuntu/Debian
Cmnd_Alias DEPLOY_APT = /usr/bin/apt-get update, /usr/bin/apt-get install *
Cmnd_Alias DEPLOY_DOCKER_SETUP = /usr/sbin/usermod -aG docker *, /usr/bin/install -m 0755 -d /etc/apt/keyrings, /usr/bin/gpg --dearmor -o /etc/apt/keyrings/docker.gpg, /bin/chmod a+r /etc/apt/keyrings/docker.gpg, /usr/bin/chmod a+r /etc/apt/keyrings/docker.gpg, /usr/bin/tee /etc/apt/sources.list.d/docker.list
Cmnd_Alias DEPLOY_DIRS = /bin/mkdir -p *, /usr/bin/mkdir -p *, /bin/chown -R *, /usr/bin/chown -R *
Cmnd_Alias DEPLOY_SYSTEMCTL = /usr/bin/systemctl enable docker, /usr/bin/systemctl start docker, /usr/bin/systemctl restart docker
SUDOERS_EOF
echo "$DEPLOY_USER ALL=(ALL) NOPASSWD: DEPLOY_APT, DEPLOY_DOCKER_SETUP, DEPLOY_DIRS, DEPLOY_SYSTEMCTL" >> "$SUDOERS_FILE"
chmod 440 "$SUDOERS_FILE"
visudo -cf "$SUDOERS_FILE"
print_success "Sudo настроен для $DEPLOY_USER (ограниченные права)"

print_header "3/5 — SSH ключ для GitHub Actions"

DEPLOY_HOME=$(eval echo ~$DEPLOY_USER)
SSH_DIR="$DEPLOY_HOME/.ssh"
KEY_PATH="$SSH_DIR/$SSH_KEY_NAME"

mkdir -p "$SSH_DIR"

KEY_EXISTED=false
if [ -f "$KEY_PATH" ]; then
    print_warning "SSH ключ уже существует: $KEY_PATH"
    KEY_EXISTED=true
else
    ssh-keygen -t ed25519 -C "github-actions-deploy" -f "$KEY_PATH" -N ""

    touch "$SSH_DIR/authorized_keys"
    cat "$KEY_PATH.pub" >> "$SSH_DIR/authorized_keys"
    sort -u "$SSH_DIR/authorized_keys" -o "$SSH_DIR/authorized_keys"

    print_success "SSH ключ сгенерирован"
fi

chown -R "$DEPLOY_USER:$DEPLOY_USER" "$SSH_DIR"
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

print_header "4/5 — Директория деплоя"

mkdir -p "$DEPLOY_DIR"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
print_success "Директория создана: $DEPLOY_DIR"

print_header "5/5 — Настройка файрвола (UFW)"

if ufw status | grep -q "inactive"; then
    ufw default deny incoming
    ufw default allow outgoing

    ufw allow 22/tcp      # SSH
    ufw allow 80/tcp      # HTTP
    ufw allow 443/tcp     # HTTPS / SSTP VPN
    ufw allow 992/tcp     # SoftEther
    ufw allow 5555/tcp    # SoftEther
    ufw allow 500/udp     # IPsec
    ufw allow 4500/udp    # IPsec NAT
    ufw allow 1701/udp    # L2TP
    ufw allow 1194/udp    # OpenVPN

    echo "y" | ufw enable
    print_success "Файрвол настроен"
else
    print_warning "Файрвол уже активен"
    ufw status verbose
fi

print_header "Настройка завершена!"

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo -e "${GREEN}VPS готов к деплою!${NC}"
echo ""
echo "Информация для GitHub Secrets:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  PREPROD_SERVER_IP:   ${YELLOW}$SERVER_IP${NC}"
echo -e "  PREPROD_SSH_USER:    ${YELLOW}$DEPLOY_USER${NC}"
echo -e "  PREPROD_DEPLOY_DIR:  ${YELLOW}$DEPLOY_DIR${NC}"
echo -e "  PREPROD_SSH_KEY:     ${YELLOW}(приватный ключ выше)${NC}"
echo ""
echo -e "${BLUE}Примечание: Docker будет установлен автоматически${NC}"
echo -e "${BLUE}при первом деплое через GitHub Actions (CI/CD).${NC}"
echo ""
echo "Следующий шаг:"
echo "  1. Скопируйте приватный ключ в GitHub Secret"
echo "  2. Добавьте остальные секреты (см. docs/DEPLOY_CHECKLIST.md)"
echo "  3. Сделайте git push в release/* ветку"
echo "  4. Docker установится автоматически при первом деплое"
echo ""
