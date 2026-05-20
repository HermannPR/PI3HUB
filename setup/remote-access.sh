#!/usr/bin/env bash
# Remote access: SSH hardening + Tailscale (access Pi from anywhere)
set -euo pipefail

# --- Enable SSH ---
echo "==> Enabling SSH"
sudo systemctl enable ssh
sudo systemctl start ssh

# --- SSH hardening (keep password auth for now, can disable later) ---
SSHD="/etc/ssh/sshd_config"
sudo sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' "$SSHD"
sudo sed -i 's/#MaxAuthTries.*/MaxAuthTries 5/' "$SSHD"
sudo systemctl restart ssh

# --- Tailscale (mesh VPN — access Pi from phone/laptop anywhere) ---
echo "==> Installing Tailscale"
curl -fsSL https://tailscale.com/install.sh | sh

echo ""
echo "==> Tailscale installed. To connect:"
echo "    sudo tailscale up"
echo "    (Opens browser link — authenticate with Google/GitHub/email)"
echo "    Then from any device on your Tailscale network:"
echo "    ssh pi@<tailscale-ip>   OR   ssh pi@raspberrypi.tail<xxxx>.ts.net"
echo ""
echo "==> Get Tailscale IP:  tailscale ip -4"
echo "==> Tailscale status:  tailscale status"

# --- mDNS so Pi is reachable on LAN as raspberrypi.local ---
sudo apt-get install -y avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

echo ""
echo "==> On local network: ssh pi@raspberrypi.local"
echo "==> Anywhere else:    ssh pi@<tailscale-ip>"
