#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="/var/log/geoip-update.log"

echo "========================================" >> "${LOG_FILE}"
echo "[$(date)] Starting GeoIP update..." >> "${LOG_FILE}"

if bash "${SCRIPT_DIR}/update-geoip.sh" >> "${LOG_FILE}" 2>&1; then
    echo "[$(date)] GeoIP update successful" >> "${LOG_FILE}"

    if command -v docker &> /dev/null; then
        COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"
        cd "${COMPOSE_DIR}"
        docker compose -f docker-compose.prod.yml kill -s HUP haproxy 2>> "${LOG_FILE}" || \
        docker compose -f docker-compose.prod.yml restart haproxy >> "${LOG_FILE}" 2>&1
        echo "[$(date)] HAProxy reloaded" >> "${LOG_FILE}"
    fi
else
    echo "[$(date)] ERROR: GeoIP update failed!" >> "${LOG_FILE}"
fi
