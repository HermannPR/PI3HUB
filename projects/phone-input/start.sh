#!/usr/bin/env bash
# Start phone input server
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

# Load uinput module
modprobe uinput 2>/dev/null || true

# Install deps if missing
python3 -c "import uinput, flask" 2>/dev/null || \
    pip3 install --break-system-packages flask python-uinput

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "================================"
echo "  Pi Remote Control"
echo "  Open on phone: http://$IP:5000"
echo "================================"
echo ""

sudo python3 "$DIR/server.py"
