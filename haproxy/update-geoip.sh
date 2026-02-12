#!/bin/bash
set -euo pipefail

GEOIP_DIR="/usr/local/etc/haproxy/geoip"
RIPE_URL="https://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-extended-latest"
OUTPUT_FILE="${GEOIP_DIR}/ru_networks.lst"
TEMP_FILE="${GEOIP_DIR}/ripe_data.tmp"

mkdir -p "${GEOIP_DIR}"

echo "[$(date)] Downloading RIPE NCC delegation data..."
if ! curl -sf -o "${TEMP_FILE}" "${RIPE_URL}"; then
    echo "[$(date)] ERROR: Failed to download RIPE data"
    exit 1
fi

echo "[$(date)] Extracting Russian IPv4 networks..."

python3 -c "
import ipaddress

output = []
with open('${TEMP_FILE}', 'r') as f:
    for line in f:
        parts = line.strip().split('|')
        if len(parts) >= 5 and parts[1] == 'RU' and parts[2] == 'ipv4':
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

output.sort(key=lambda x: int(ipaddress.IPv4Network(x).network_address))

with open('${OUTPUT_FILE}', 'w') as f:
    f.write('\n'.join(output) + '\n')

print(f'[INFO] Total Russian CIDR networks: {len(output)}')
"

rm -f "${TEMP_FILE}"

echo "[$(date)] Done! Output: ${OUTPUT_FILE}"
