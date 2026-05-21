#!/usr/bin/env bash
# Phone gamepad web app — phone browser → Pi virtual controller via uinput
set -euo pipefail

echo "==> Installing dependencies"
sudo apt-get install -y python3 python3-pip
pip3 install --break-system-packages flask python-uinput

echo "==> Loading uinput kernel module"
sudo modprobe uinput
echo "uinput" | sudo tee -a /etc/modules

echo "==> Setting uinput permissions"
sudo chmod 666 /dev/uinput

echo "==> Installing gamepad server"
mkdir -p ~/PI3/gamepad
cp "$(dirname "$0")/../gamepad/server.py" ~/PI3/gamepad/
cp "$(dirname "$0")/../gamepad/pad.html" ~/PI3/gamepad/

echo ""
echo "==> Phone Gamepad setup done."
echo "    Start server: sudo python3 ~/PI3/gamepad/server.py"
echo "    Open on phone: http://$(hostname -I | awk '{print $1}'):5000"
