#!/usr/bin/env bash
# Audio / music tools for Pi 3
set -euo pipefail

echo "==> Installing audio stack"
sudo apt-get install -y \
    jackd2 \
    qjackctl \
    pulseaudio \
    alsa-utils \
    sox \
    ffmpeg \
    fluidsynth \
    fluid-soundfont-gm \
    pure-data \
    supercollider \
    sonic-pi \
    python3-pyaudio \
    python3-mido \
    python3-rtmidi

echo "==> Adding user to audio group"
sudo usermod -aG audio "$USER"

echo "==> Audio tools installed. Log out and back in for group change."
