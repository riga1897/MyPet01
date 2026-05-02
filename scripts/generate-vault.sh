#!/bin/bash
# generate-vault.sh — генерирует ansible/vault.yml из переменных окружения
#
# Использование:
#   Локально (Windows Git Bash / Linux / Mac):
#     cp .env.vault.example .env.vault
#     # заполни .env.vault реальными значениями
#     source .env.vault && bash scripts/generate-vault.sh
#
#   В CI/CD (GitHub Actions):
#     вызывается автоматически на шаге "Generate vault.yml from secrets"

set -euo pipefail

VAULT_FILE="ansible/vault.yml"

# Проверить обязательные переменные
REQUIRED=(
    VAULT_DB_PASSWORD
    VAULT_PG_REPLICATION_PASSWORD
    VAULT_GRAFANA_PASSWORD
    VAULT_SEMAPHORE_ADMIN_PASSWORD
    VAULT_SSH_PRIVATE_KEY
)

MISSING=""
for VAR in "${REQUIRED[@]}"; do
    [ -z "${!VAR:-}" ] && MISSING="$MISSING $VAR"
done

if [ -n "$MISSING" ]; then
    echo "Ошибка: не заданы переменные окружения:$MISSING"
    echo "Скопируй .env.vault.example → .env.vault и заполни значения."
    exit 1
fi

cat > "$VAULT_FILE" << EOF
# Сгенерировано автоматически — не редактировать вручную
# Источник: GitHub Secrets (CI/CD) или .env.vault (локально)
# Регенерировать: source .env.vault && bash scripts/generate-vault.sh

vault_secret_key: "${VAULT_SECRET_KEY:-}"
vault_allowed_hosts: "${VAULT_ALLOWED_HOSTS:-www.mine-craft.su,mine-craft.su}"
vault_csrf_trusted_origins: "${VAULT_CSRF_TRUSTED_ORIGINS:-https://www.mine-craft.su,https://mine-craft.su}"

vault_db_user: "${VAULT_DB_USER:-blog_user}"
vault_db_password: "${VAULT_DB_PASSWORD}"
vault_db_name: "${VAULT_DB_NAME:-blog_db}"

vault_pg_replication_password: "${VAULT_PG_REPLICATION_PASSWORD}"

vault_grafana_password: "${VAULT_GRAFANA_PASSWORD}"

vault_s3_access_key: "${VAULT_S3_ACCESS_KEY:-}"
vault_s3_secret_key: "${VAULT_S3_SECRET_KEY:-}"

vault_telegram_token: "${VAULT_TELEGRAM_TOKEN:-}"
vault_telegram_chat_id: "${VAULT_TELEGRAM_CHAT_ID:-}"

vault_ssh_private_key: |
$(echo "${VAULT_SSH_PRIVATE_KEY}" | sed 's/^/  /')

vault_semaphore_admin_user:        "${VAULT_SEMAPHORE_ADMIN_USER:-admin}"
vault_semaphore_admin_password:    "${VAULT_SEMAPHORE_ADMIN_PASSWORD}"
vault_semaphore_admin_email:       "${VAULT_SEMAPHORE_ADMIN_EMAIL:-admin@mine-craft.su}"
vault_semaphore_secret_key:        "4d081d10d650a0fd41b7cf656dabd6df"
vault_semaphore_cookie_hash:       "9b1ed3874ff13809c5abbfc657ba8425"
vault_semaphore_cookie_encryption: "a4a162417122507eecaa94d4d43b7ece"
EOF

echo "vault.yml сгенерирован: $VAULT_FILE"
