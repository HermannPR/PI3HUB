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

# yt-dlp required for YT tab
command -v yt-dlp >/dev/null 2>&1 || pip3 install --break-system-packages yt-dlp 2>/dev/null || true

# Auto-start Claude Code in tmux (60x30 = phone-optimised width)
TMUX_SOCK=/tmp/tmux-1000/default
if ! sudo -u peepo tmux -S "$TMUX_SOCK" has-session -t setup 2>/dev/null; then
    sudo -u peepo tmux -S "$TMUX_SOCK" new-session -d -s setup -x 60 -y 30
    sudo -u peepo tmux -S "$TMUX_SOCK" new-window -t setup -n claude
    sudo -u peepo tmux -S "$TMUX_SOCK" send-keys -t setup:claude 'claude' Enter
fi
# Trust-prompt watcher handled by server.py _watch_trust() thread

sudo python3 "$DIR/server.py"
