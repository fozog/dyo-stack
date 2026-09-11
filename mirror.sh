#!/usr/bin/env bash
#
# Configure physical interface queues and mirror traffic to a multi-queue VM interface (vnet2)

set -euo pipefail

# --- CONFIGURATION ---
SOURCE_IF="eth2"
TARGET_IF="vnet2"
QUEUES=2
# ---------------------

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "Error: This script must be run as root (use sudo)." >&2
        exit 1
    fi
}

start_mirror() {
    echo "[+] Configuring ${SOURCE_IF} with ${QUEUES} combined hardware queues..."
    ethtool -L "${SOURCE_IF}" combined "${QUEUES}" 2>/dev/null || echo "Warning: Driver may not support dynamic channel adjustment via ethtool."

    echo "[+] Starting bidirectional mirror: ${SOURCE_IF} -> ${TARGET_IF}"

    # 1. Ingress Setup (traffic coming INTO eth2)
#    tc qdisc add dev "${SOURCE_IF}" handle ffff: ingress 2>/dev/null || true
    if ! tc qdisc show dev "${SOURCE_IF}" | grep -q "ingress"; then
        sudo tc qdisc add dev "${SOURCE_IF}" handle ffff: ingress
    fi
    tc filter add dev "${SOURCE_IF}" parent ffff: \
        protocol all \
        u32 match u32 0 0 \
        action mirred egress mirror dev "${TARGET_IF}"

    # 2. Egress Setup (traffic going OUT of eth2)
    tc qdisc add dev "${SOURCE_IF}" clsact 2>/dev/null || true
    tc filter add dev "${SOURCE_IF}" egress \
        protocol all \
        u32 match u32 0 0 \
        action mirred egress mirror devynth="${TARGET_IF}" 2>/dev/null || \
    tc filter add dev "${SOURCE_IF}" egress \
        protocol all \
        u32 match u32 0 0 \
        action mirred egress mirror dev "${TARGET_IF}"

    echo "[+] Mirror active! Packets will distribute across the multi-queue tap."
}

stop_mirror() {
    echo "[-] Removing mirroring rules from ${SOURCE_IF}..."
    tc qdisc del dev "${SOURCE_IF}" handle ffff: ingress 2>/dev/null || true
    tc qdisc del dev "${SOURCE_IF}" clsact 2>/dev/null || true
    echo "[-] Mirror stopped."
}

status_mirror() {
    echo "=== Hardware Queue Status for ${SOURCE_IF} ==="
    ethtool -l "${SOURCE_IF}" 2> /dev/null || true
    echo ""
    echo "=== Active Filters on ${SOURCE_IF} ==="
    tc filter show dev "${SOURCE_IF}" ingress || true
    tc filter show dev "${SOURCE_IF}" egress || true
}

check_root

case "${1:-}" in
    start)
        start_mirror
        ;;
    stop)
        stop_mirror
        ;;
    status)
        status_mirror
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
