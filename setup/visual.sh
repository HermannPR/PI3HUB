#!/usr/bin/env bash
# Visual / generative graphics tools for Pi 3
set -euo pipefail

echo "==> Installing visual tools"
sudo apt-get install -y \
    fbi \
    fim \
    mpv \
    vlc \
    python3-pygame \
    python3-pil \
    python3-numpy \
    python3-opencv \
    glsl-tools \
    mesa-utils \
    libgl1-mesa-dri

echo "==> Installing Python creative libs"
pip3 install --break-system-packages \
    drawsvg \
    py5 \
    colour \
    perlin-noise \
    rpi-ws281x

echo "==> Installing Processing (headless-capable)"
PROCESSING_VERSION="4.3"
wget -q "https://github.com/processing/processing4/releases/download/processing-${PROCESSING_VERSION}/processing-${PROCESSING_VERSION}-linux-arm64.tgz" \
    -O /tmp/processing.tgz
tar -xzf /tmp/processing.tgz -C "$HOME"
echo "Processing extracted to $HOME/processing-${PROCESSING_VERSION}"

echo "==> Visual tools installed."
