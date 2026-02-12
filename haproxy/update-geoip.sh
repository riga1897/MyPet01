#!/bin/bash
set -euo pipefail

RIPE_URL="https://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-extended-latest"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ ! -d "${SCRIPT_DIR}/geoip" ] && [ ! -d "${SCRIPT_DIR}/blacklist" ]; then
    echo "[ERROR] Скрипт запущен из неожиданной директории: ${SCRIPT_DIR}"
    echo "[ERROR] Ожидается запуск из <project>/haproxy/"
    exit 1
fi

GEOIP_DIR="${SCRIPT_DIR}/geoip"
OUTPUT_FILE="${GEOIP_DIR}/ru_networks.lst"
TEMP_FILE="/tmp/ripe_data_$$.tmp"
LOG_FILE="/var/log/update-geoip.log"

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

cleanup() {
    rm -f "$TEMP_FILE"
}
trap cleanup EXIT

mkdir -p "${GEOIP_DIR}"

log "Скачивание данных RIPE NCC..."
if ! curl -sf --connect-timeout 30 --max-time 120 -o "${TEMP_FILE}" "${RIPE_URL}"; then
    log "ОШИБКА: Не удалось скачать данные RIPE"
    exit 1
fi

log "Извлечение российских IPv4 сетей..."

RESULT=$(python3 -c "
import ipaddress, sys

output = []
with open('${TEMP_FILE}', 'r') as f:
    for line in f:
        parts = line.strip().split('|')
        if len(parts) >= 5 and parts[1] == 'RU' and parts[2] == 'ipv4':
            try:
                start_ip = parts[3]
                count = int(parts[4])
                start_int = int(ipaddress.IPv4Address(start_ip))
                end_int = start_int + count - 1
                networks = ipaddress.summarize_address_range(
                    ipaddress.IPv4Address(start_int),
                    ipaddress.IPv4Address(end_int)
                )
                for net in networks:
                    output.append(str(net))
            except (ValueError, TypeError) as e:
                print(f'Пропуск некорректной записи: {line.strip()} ({e})', file=sys.stderr)

output.sort(key=lambda x: int(ipaddress.IPv4Network(x).network_address))

with open('${OUTPUT_FILE}', 'w') as f:
    f.write('\n'.join(output) + '\n')

print(len(output))
")

NETWORK_COUNT="${RESULT}"
log "Сгенерировано ${NETWORK_COUNT} CIDR-сетей в ${OUTPUT_FILE}"

if [ "${NETWORK_COUNT}" -lt 100 ]; then
    log "ПРЕДУПРЕЖДЕНИЕ: Слишком мало сетей (${NETWORK_COUNT}). Возможна ошибка данных RIPE."
fi

COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"
if [ -f "${COMPOSE_FILE}" ]; then
    if docker compose -f "${COMPOSE_FILE}" ps haproxy 2>/dev/null | grep -q "Up\|running"; then
        log "Перезапуск HAProxy для применения нового списка..."
        docker compose -f "${COMPOSE_FILE}" kill -s HUP haproxy 2>/dev/null || \
            docker compose -f "${COMPOSE_FILE}" restart haproxy
        log "HAProxy перезапущен"
    else
        log "HAProxy не запущен — пропуск перезапуска"
    fi
else
    log "docker-compose.prod.yml не найден — пропуск перезапуска HAProxy"
fi

log "Обновление GeoIP завершено успешно"
