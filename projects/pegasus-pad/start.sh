#!/usr/bin/env bash
# Pegasus Frontend gamepad companion launcher
# Usage: sudo bash start.sh
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

# Install Flask if missing (no uinput needed — only xdotool)
python3 -c "import flask" 2>/dev/null || \
    pip3 install --break-system-packages flask 2>/dev/null

# Install qrcode for terminal QR (optional)
python3 -c "import qrcode" 2>/dev/null || \
    pip3 install --break-system-packages qrcode 2>/dev/null || true

# Make sure xdotool is present
command -v xdotool >/dev/null 2>&1 || apt-get install -y xdotool >/dev/null 2>&1 || \
    echo "  WARNING: xdotool not found — input won't work"

IP=$(hostname -I | awk '{print $1}')

echo ""
echo "  ╔══════════════════════════════╗"
echo "  ║   PEGASUS GAMEPAD COMPANION  ║"
echo "  ╠══════════════════════════════╣"
echo "  ║                              ║"
printf "  ║  Phone URL: %-17s║\n" "http://$IP:5001"
echo "  ║                              ║"
echo "  ╚══════════════════════════════╝"
echo ""

# QR code
python3 - "$IP" <<'PYEOF'
import sys, socket
try:
    import qrcode
    url = f"http://{sys.argv[1]}:5001"
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)
    print()
except Exception:
    pass
PYEOF

echo "  Controls:"
echo "    PEGASUS mode : D-pad=arrows  A=Enter  B=Esc  X=F1  Y=F2"
echo "                   L1/R1=PgDn/Up  L2/R2=prev/next collection"
echo "    GAME mode    : D-pad=arrows  A=x  B=z  X=s  Y=a"
echo "                   L1=q  R1=w  L2=e  R2=r  (RetroArch defaults)"
echo ""
echo "  Ctrl+C to stop"
echo ""

sudo python3 "$DIR/server.py"
