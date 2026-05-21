#!/usr/bin/env bash
# Base system setup for Pi 3 creative dev
set -euo pipefail

echo "==> Updating system"
sudo apt-get update && sudo apt-get upgrade -y

echo "==> Installing essential tools"
sudo apt-get install -y \
    git \
    curl \
    wget \
    vim \
    tmux \
    htop \
    tree \
    unzip \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    i2c-tools \
    python3-gpiozero \
    python3-lgpio

echo "==> Enabling interfaces (I2C, SPI, camera)"
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_camera 0

echo "==> Base setup done. Reboot recommended."
