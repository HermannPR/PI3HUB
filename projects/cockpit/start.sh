#!/usr/bin/env bash
# JarvisPi3 — unified control server launcher
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

# Deps
python3 -c "import flask, flask_sock" 2>/dev/null || \
    pip3 install --break-system-packages flask flask-sock

python3 -c "import uinput" 2>/dev/null || \
    pip3 install --break-system-packages python-uinput 2>/dev/null || true

python3 -c "from PIL import Image" 2>/dev/null || \
    pip3 install --break-system-packages pillow 2>/dev/null || true

command -v xdotool >/dev/null 2>&1 || apt-get install -y xdotool >/dev/null 2>&1 || true
modprobe uinput 2>/dev/null || true

# QR code
python3 -c "import qrcode" 2>/dev/null || \
    pip3 install --break-system-packages qrcode 2>/dev/null || true

IP=$(hostname -I | awk '{print $1}')
URL="http://$IP:5000"

# Get git commit count as peepo (git rejects repo owned by peepo when run as root)
GIT_N=$(runuser -u peepo -- git -C "$(dirname "$0")" rev-list --count HEAD 2>/dev/null || echo 0)
export PI_VERSION="1.${GIT_N}"

echo ""
echo "  ╔══════════════════════════════╗"
echo "  ║        JARVIS  PI3           ║"
echo "  ╠══════════════════════════════╣"
printf "  ║  Phone: %-22s║\n" "$URL"
echo "  ╚══════════════════════════════╝"
echo ""

python3 - "$URL" <<'PYEOF'
import sys
try:
    import qrcode
    qr = qrcode.QRCode(border=1)
    qr.add_data(sys.argv[1])
    qr.make(fit=True)
    qr.print_ascii(invert=True)
    print()
except Exception:
    pass
PYEOF

echo "  Modes:  CLAUDE DEV  GAMING  DESKTOP  HEADLESS"
echo "  Boot:   http://localhost:5000/boot"
echo "  Ctrl+C to stop"
echo ""

export TAMAGO_URL="${TAMAGO_URL:-https://mildred-pierce.vercel.app}"

exec python3 "$DIR/server.py"
