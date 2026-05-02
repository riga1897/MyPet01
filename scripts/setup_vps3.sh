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

print_success() { echo -e "${GREEN}[OK] $1${NC}"; }
print_warning() { echo -e "${YELLOW}[!] $1${NC}"; }
print_error()   { echo -e "${RED}[ERROR] $1${NC}"; }

if [ "$(id -u)" -ne 0 ]; then
    print_error "Скрипт должен запускаться от root"
    exit 1
fi

print_header "MyPet01 — Настройка VPS3 (Management)"

echo "VPS3 выполняет роли:"
echo "  - Ansible control node (провизионинг VPS1 и VPS2)"
echo "  - Prometheus + Grafana (мониторинг)"
echo "  - Управление GeoIP-обновлениями"
echo ""

print_header "1/5 — Обновление системы"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y -o Dpkg::Options::="--force-confold" -o Dpkg::Options::="--force-confdef"
print_success "Система обновлена"

print_header "2/5 — Установка базовых пакетов"

apt-get install -y curl ufw fail2ban python3 python3-pip
print_success "Базовые пакеты установлены"

print_header "3/5 — Генерация ANSIBLE_SSH_KEY"

ANSIBLE_KEY_PATH="/root/.ssh/ansible_key"
mkdir -p /root/.ssh
chmod 700 /root/.ssh

if [ -f "$ANSIBLE_KEY_PATH" ]; then
    print_warning "Старый ключ найден — перегенерирую"
fi
rm -f "$ANSIBLE_KEY_PATH" "$ANSIBLE_KEY_PATH.pub"

ssh-keygen -t ed25519 -C "ansible-ci-cd" -f "$ANSIBLE_KEY_PATH" -N ""
print_success "ANSIBLE_SSH_KEY сгенерирован: $ANSIBLE_KEY_PATH"

cat "$ANSIBLE_KEY_PATH.pub" >> /root/.ssh/authorized_keys
sort -u /root/.ssh/authorized_keys -o /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys
print_success "Публичный ключ добавлен в authorized_keys VPS3"

print_header "4/5 — Базовое hardening (ufw + SSH)"

ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 9090/tcp comment "Prometheus (только для своих)"
ufw allow 3000/tcp comment "Grafana (только для своих)"
echo 'y' | ufw enable
print_success "UFW настроен"

SSHD_CONFIG="/etc/ssh/sshd_config"
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' "$SSHD_CONFIG"
systemctl restart sshd 2>/dev/null || systemctl restart ssh 2>/dev/null
print_success "Вход по паролю SSH отключён"

print_header "5/5 — Настройка fail2ban"

systemctl enable fail2ban
systemctl start fail2ban
print_success "Fail2ban запущен"

SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  ВАЖНО: выполни эти шаги после завершения скрипта           ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Шаг 1 — Добавить публичный ключ на VPS1 и VPS2:${NC}"
echo ""
echo -e "  ${GREEN}Публичный ключ (скопируй):${NC}"
cat "$ANSIBLE_KEY_PATH.pub"
echo ""
echo "  На VPS1 и VPS2 выполни:"
echo -e "  ${YELLOW}echo '<публичный ключ выше>' >> ~/.ssh/authorized_keys${NC}"
echo "  (или используй setup_vps.sh — он добавит ключ при настройке)"
echo ""
echo -e "${BLUE}Шаг 2 — Добавить в GitHub Secrets:${NC}"
echo ""
echo -e "  ${YELLOW}VPS3_SERVER_IP:${NC}        $SERVER_IP"
echo -e "  ${YELLOW}VPS3_SSH_USER:${NC}         root"
echo -e "  ${YELLOW}ANSIBLE_SSH_KEY:${NC}       (приватный ключ ниже — скопировать целиком)"
echo -e "  ${YELLOW}ANSIBLE_VAULT_PASSWORD:${NC} придумать и сохранить"
echo ""
echo -e "${GREEN}=== ПРИВАТНЫЙ КЛЮЧ (ANSIBLE_SSH_KEY) ===${NC}"
echo -e "${GREEN}--- НАЧАЛО КЛЮЧА ---${NC}"
cat "$ANSIBLE_KEY_PATH"
echo -e "${GREEN}--- КОНЕЦ КЛЮЧА ---${NC}"
echo ""
echo -e "${BLUE}Шаг 3 — Запустить Ansible провизионинг:${NC}"
echo "  GitHub → Actions → MyPet01 CI/CD Pipeline → Run workflow"
echo "  target: all"
echo ""
echo -e "${GREEN}VPS3 готов!${NC}"
