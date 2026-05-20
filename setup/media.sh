#!/usr/bin/env bash
# Media center / kiosk setup for Pi 3
set -euo pipefail

echo "==> Installing media tools"
sudo apt-get install -y \
    kodi \
    mpv \
    feh \
    chromium-browser \
    xorg \
    openbox \
    lightdm \
    unclutter

echo "==> Kiosk mode: auto-login + launch Chromium fullscreen"
# Edit /etc/lightdm/lightdm.conf to autologin
sudo sed -i 's/#autologin-user=/autologin-user=pi/' /etc/lightdm/lightdm.conf
sudo sed -i 's/#autologin-user-timeout=0/autologin-user-timeout=0/' /etc/lightdm/lightdm.conf

AUTOSTART_DIR="$HOME/.config/openbox"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/autostart" << 'EOF'
# Hide cursor after 1s idle
unclutter -idle 1 &
# Launch Chromium in kiosk mode — edit URL below
chromium-browser --kiosk --disable-infobars --noerrdialogs \
    --disable-session-crashed-bubble \
    "http://localhost:8080" &
EOF

echo "==> Media/kiosk setup done. Edit $AUTOSTART_DIR/autostart to set your kiosk URL."
