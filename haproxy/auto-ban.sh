#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ ! -d "${SCRIPT_DIR}/blacklist" ]; then
    echo "[ERROR] Скрипт запущен из неожиданной директории: ${SCRIPT_DIR}"
    echo "[ERROR] Ожидается запуск из <project>/haproxy/"
    exit 1
fi

BLACKLIST_FILE="${SCRIPT_DIR}/blacklist/blocked_ips.lst"
WHITELIST_FILE="${SCRIPT_DIR}/blacklist/whitelist_ips.lst"
LOG_FILE="/var/log/haproxy-autoban.log"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"

BAN_THRESHOLD="${BAN_THRESHOLD:-10}"
LOG_WINDOW="${LOG_WINDOW:-1h}"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

if [ ! -f "${COMPOSE_FILE}" ]; then
    log "ОШИБКА: ${COMPOSE_FILE} не найден"
    exit 1
fi

if ! docker compose -f "${COMPOSE_FILE}" ps haproxy 2>/dev/null | grep -q "Up\|running"; then
    log "HAProxy не запущен — пропуск"
    exit 0
fi

WHITELIST_IPS=""
if [ -f "${WHITELIST_FILE}" ]; then
    WHITELIST_IPS=$(grep -vE '^\s*(#|$)' "${WHITELIST_FILE}" 2>/dev/null | tr '\n' '|' | sed 's/|$//')
fi

EXISTING_IPS=""
if [ -f "${BLACKLIST_FILE}" ]; then
    EXISTING_IPS=$(grep -vE '^\s*(#|$)' "${BLACKLIST_FILE}" 2>/dev/null | tr '\n' '|' | sed 's/|$//')
fi

log "=== Запуск автобана (порог: ${BAN_THRESHOLD} блокировок за ${LOG_WINDOW}) ==="

LOGS_RAW=$(docker compose -f "${COMPOSE_FILE}" logs --since="${LOG_WINDOW}" --no-log-prefix haproxy 2>/dev/null || true)

if [ -z "${LOGS_RAW}" ]; then
    log "Нет логов HAProxy за последний период"
    exit 0
fi

NEW_BANS=$(echo "${LOGS_RAW}" | python3 -c "
import sys
import re
from collections import defaultdict

ban_threshold = int('${BAN_THRESHOLD}')

whitelist_str = '${WHITELIST_IPS}'
whitelist = set(whitelist_str.split('|')) if whitelist_str else set()

existing_str = '${EXISTING_IPS}'
existing = set(existing_str.split('|')) if existing_str else set()

ip_403_count = defaultdict(int)
ip_paths = defaultdict(set)

for line in sys.stdin:
    line = line.strip()

    m = re.match(r'^(\d+\.\d+\.\d+\.\d+):\d+\s+\[.*?\]\s+\S+\s+\S+\s+\S+\s+(\d{3})\s', line)
    if m:
        ip = m.group(1)
        status = m.group(2)
        if status == '403':
            ip_403_count[ip] += 1
            path_m = re.search(r'\"(?:GET|POST|HEAD|PUT|DELETE|OPTIONS|PATCH)\s+(\S+)', line)
            if path_m:
                ip_paths[ip].add(path_m.group(1))
        continue

    m2 = re.match(r'^(\d+\.\d+\.\d+\.\d+):\d+\s+\[', line)
    if m2:
        continue

new_bans = []
for ip, count in sorted(ip_403_count.items(), key=lambda x: -x[1]):
    if count >= ban_threshold and ip not in whitelist and ip not in existing:
        paths = ', '.join(sorted(ip_paths[ip])[:5])
        new_bans.append(f'{ip}|{count}|{paths}')

for b in new_bans:
    print(b)
")

if [ -z "${NEW_BANS}" ]; then
    log "Новых IP для бана не найдено"
    exit 0
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
BAN_COUNT=0

echo "" >> "${BLACKLIST_FILE}"
echo "# --- Автобан ${TIMESTAMP} ---" >> "${BLACKLIST_FILE}"

while IFS='|' read -r ip count paths; do
    echo "${ip}" >> "${BLACKLIST_FILE}"
    log "ЗАБАНЕН: ${ip} (${count} блокировок, пути: ${paths})"
    BAN_COUNT=$((BAN_COUNT + 1))
done <<< "${NEW_BANS}"

log "Добавлено ${BAN_COUNT} IP в чёрный список"

log "Перезагрузка HAProxy..."
if docker compose -f "${COMPOSE_FILE}" kill -s HUP haproxy 2>/dev/null; then
    log "HAProxy перезагружен (HUP)"
else
    docker compose -f "${COMPOSE_FILE}" restart haproxy 2>/dev/null || true
    log "HAProxy перезапущен (restart)"
fi

log "=== Автобан завершён: +${BAN_COUNT} IP ==="
