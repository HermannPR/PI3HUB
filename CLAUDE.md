# Claude Code — Raspberry Pi 3 Creative Dev

## Hardware

- **Device:** Raspberry Pi 3 Model B / B+
- **CPU:** ARM Cortex-A53 @ 1.4GHz, 4 cores (armv8 / arm64)
- **RAM:** 1GB LPDDR2 — conserve memory; avoid large in-process data
- **GPU:** VideoCore IV — no CUDA/ROCm; use CPU-only ML libs
- **Storage:** microSD (slow random I/O) — batch writes, avoid frequent small writes
- **OS:** Raspberry Pi OS (Debian Bookworm, 64-bit)

## GPIO / Hardware interfaces

- GPIO via `gpiozero` (preferred) or `RPi.GPIO`
- I2C: `/dev/i2c-1` — enabled via `raspi-config`
- SPI: `/dev/spidev0.0` — enabled via `raspi-config`
- PWM on GPIO 18 — conflicts with onboard audio; pick one
- NeoPixel/WS281x: `rpi-ws281x` lib, needs `sudo`
- Camera: `picamera2` lib

## Python environment

- Python 3.11 (system)
- Install packages: `pip3 install --break-system-packages <pkg>`
- Prefer lightweight libs — no PyTorch, no TensorFlow full (use `tflite-runtime`)
- Good choices: `numpy`, `pygame`, `gpiozero`, `pillow`, `opencv-python-headless`, `mido`

## Audio

- ALSA + JACK2 available
- FluidSynth for MIDI → audio
- Sonic Pi, SuperCollider, Pure Data installed
- 3.5mm jack OR HDMI audio (set `hdmi_drive=2` in config.txt)

## Display

- HDMI output, default 1080p (can reduce for performance)
- Framebuffer: `/dev/fb0`
- X11 desktop available; pygame can run fullscreen
- VNC enabled for remote desktop

## Remote access

- SSH: `pi@raspberrypi.local` (LAN) or `pi@<tailscale-ip>` (anywhere)
- Tailscale installed for mesh VPN
- tmux for persistent sessions — always work inside tmux
- KDE Connect for phone keyboard/mouse input

## Performance constraints

- Keep processes under ~700MB RAM total
- Avoid parallel heavy compilation; use `-j2` max for make
- Prefer `opencv-python-headless` over full OpenCV (no Qt dep)
- Use `pygame` display in 720p or lower for smooth framerates
- CPU-only inference only; tflite-runtime for ML

## Project structure

```
PI3/
├── CLAUDE.md          ← you are here
├── setup/             ← install scripts (run on Pi)
├── config/            ← /boot/config.txt snippets, dotfiles
└── examples/          ← working code examples
```

## Commands to know

```bash
pinout                          # GPIO diagram in terminal
raspi-config                    # Pi config tool
vcgencmd measure_temp           # CPU temperature
vcgencmd get_throttled          # check for thermal throttling
gpio readall                    # all pin states
i2cdetect -y 1                  # scan I2C bus
aplay -l                        # list audio devices
tmux new -s work / attach -t work
tailscale status
kdeconnect-cli --list-devices
```

## Preferred patterns

- Use `gpiozero` not `RPi.GPIO` (cleaner API, better cleanup)
- Use `python3 -m venv venv` for isolated deps when needed
- Scripts that touch GPIO: note they may need `sudo`
- Test with small data before full runs (SD card I/O is slow)
- For display projects: pygame fullscreen at 30fps is comfortable
