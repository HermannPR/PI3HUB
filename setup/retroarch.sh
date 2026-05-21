#!/usr/bin/env bash
# RetroArch + cores for Pi 3 — NES, SNES, GBA, PS1, N64
set -euo pipefail

echo "==> Installing RetroArch"
sudo apt-get update
sudo apt-get install -y retroarch retroarch-assets

echo "==> Installing emulator cores"
sudo apt-get install -y \
    libretro-nestopia \
    libretro-snes9x \
    libretro-mgba \
    libretro-pcsx-rearmed \
    libretro-mupen64plus

echo "==> Creating ROM directories"
mkdir -p ~/roms/{nes,snes,gba,ps1,n64}

echo "==> Configuring RetroArch for Pi 3 performance"
RACONF="$HOME/.config/retroarch/retroarch.cfg"
mkdir -p "$(dirname "$RACONF")"

cat > "$RACONF" << 'EOF'
video_driver = "gl"
video_fullscreen = true
video_vsync = true
video_smooth = false
video_scale_integer = true
audio_driver = "alsa"
input_driver = "udev"
# Pi 3 — cap at 60fps, no filtering
video_max_swapchain_images = 2
video_threaded = true
EOF

echo ""
echo "==> RetroArch installed."
echo "    Put ROMs in ~/roms/<system>/"
echo "    Launch: retroarch"
echo "    Or per-game: retroarch -L /usr/lib/libretro/nestopia_libretro.so ~/roms/nes/game.nes"
echo ""
echo "Core paths:"
echo "  NES:  /usr/lib/libretro/nestopia_libretro.so"
echo "  SNES: /usr/lib/libretro/snes9x_libretro.so"
echo "  GBA:  /usr/lib/libretro/mgba_libretro.so"
echo "  PS1:  /usr/lib/libretro/pcsx_rearmed_libretro.so"
echo "  N64:  /usr/lib/libretro/mupen64plus_next_libretro.so"
