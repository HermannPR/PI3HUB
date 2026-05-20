#!/usr/bin/env bash
# LED / hardware control for Pi 3 (NeoPixel, WS281x, PWM)
set -euo pipefail

echo "==> Installing LED dependencies"
sudo apt-get install -y \
    python3-dev \
    scons \
    swig

pip3 install --break-system-packages \
    rpi-ws281x \
    adafruit-circuitpython-neopixel \
    adafruit-circuitpython-led-animation \
    gpiozero

echo "==> Disabling audio (conflicts with PWM on GPIO 18)"
# ws281x on GPIO 18 requires disabling onboard audio
sudo sed -i 's/dtparam=audio=on/dtparam=audio=off/' /boot/config.txt

echo "==> LED tools installed. Reboot required (audio disabled)."
