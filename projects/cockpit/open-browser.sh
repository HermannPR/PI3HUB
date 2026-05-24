#!/usr/bin/env bash
# Wait for nexus server then launch pygame boot display
# Replaces Chromium kiosk — much lighter on Pi 3

DIR="$(cd "$(dirname "$0")" && pwd)"

until curl -sf http://localhost:5000/ping >/dev/null 2>&1; do sleep 1; done

exec python3 "$DIR/boot_display.py"
