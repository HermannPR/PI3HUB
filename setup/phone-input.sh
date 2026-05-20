#!/usr/bin/env bash
# Phone as keyboard/mouse/touchpad for Pi 3
# Method 1: KDE Connect (recommended — open source, Android + iOS)
# Method 2: VNC (built into Pi OS — full remote desktop)
set -euo pipefail

# =========================================================
# METHOD 1: KDE Connect
# Phone app: "KDE Connect" (Android/F-Droid) or "KDE Connect" (iOS)
# Features: mouse, keyboard, clipboard sync, media control,
#           file transfer, notifications, run commands
# =========================================================
echo "==> Installing KDE Connect"
sudo apt-get install -y kdeconnect

# Open firewall ports for KDE Connect
sudo ufw allow 1714:1764/tcp 2>/dev/null || true
sudo ufw allow 1714:1764/udp 2>/dev/null || true

echo ""
echo "==> KDE Connect setup:"
echo "    1. Install 'KDE Connect' app on your phone (Play Store / App Store)"
echo "    2. Both phone and Pi must be on same WiFi"
echo "    3. On Pi: kdeconnect-app  (or run headless: kdeconnect-cli --list-devices)"
echo "    4. Pair from phone app"
echo "    5. Enable 'Remote Input' plugin on phone → touchpad + keyboard"
echo ""
echo "==> CLI control examples:"
echo "    kdeconnect-cli --list-devices"
echo "    kdeconnect-cli --device <id> --ping"
echo "    kdeconnect-cli --device <id> --share-text 'hello'"

# =========================================================
# METHOD 2: VNC (full desktop remote — see Pi screen on phone)
# Phone app: "RealVNC Viewer" or "bVNC"
# =========================================================
echo ""
echo "==> Enabling VNC server (built into Pi OS)"
sudo raspi-config nonint do_vnc 0

echo ""
echo "==> VNC setup:"
echo "    1. Install 'RealVNC Viewer' on phone"
echo "    2. Connect to: raspberrypi.local  (or Tailscale IP for remote)"
echo "    3. Default user: pi  (or your username)"
echo ""
echo "==> VNC runs on port 5900"

# =========================================================
# BONUS: x11vnc for custom resolution / headless
# =========================================================
sudo apt-get install -y x11vnc
x11vnc -storepasswd "$HOME/.vnc/passwd" 2>/dev/null || true

echo ""
echo "==> All input methods installed."
echo "    Recommended for creative work: KDE Connect (low latency touchpad+keyboard)"
echo "    Recommended for full control:  VNC (see and control full desktop)"
