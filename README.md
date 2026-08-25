# PI3 — Raspberry Pi 3 Creative Dev Kit

Toolkit for turning a Raspberry Pi 3 (1 GB RAM) into a creative dev machine: Claude Code on the Pi, phone-controlled UIs (Python/Flask), GPIO/audio/media setup, and retro gaming.

## What it is

- Flask phone-control servers that turn the phone into a keyboard/mouse, a gamepad, and a unified "cockpit" for controlling the Pi (including Claude Code sessions in tmux).
- Shell setup scripts and systemd units for installing and auto-starting everything.
- `CLAUDE.md` documents the hardware constraints and the phone-UI output conventions Claude Code must follow on this device; `config/phone-ui-rules.md` is the same style guide for the phone wrapper (numbered options, `[y/n]` confirmations, `✔ Done.` / `✗ Failed:` signals).

## Hardware (summary — full details in CLAUDE.md)

- Raspberry Pi 3 Model B/B+, 1 GB RAM (keep processes under ~700 MB), arm64, microSD storage.
- GPIO (prefer `gpiozero`), I2C `/dev/i2c-1`, SPI, PWM (conflicts with onboard audio), NeoPixel (`rpi-ws281x`, needs sudo), camera (`picamera2`).
- Audio: ALSA + JACK2, FluidSynth, Sonic Pi, SuperCollider, Pure Data.
- Display: HDMI 1080p, framebuffer `/dev/fb0`, VNC; remote access via SSH, Tailscale mesh VPN, KDE Connect.

## Projects

| Project | Port | What it does | Run |
| --- | --- | --- | --- |
| `projects/cockpit` | 5000 | Unified phone control: modes CLAUDE DEV / GAMING / DESKTOP / HEADLESS, uinput mouse+keyboard, streams the `setup:claude` tmux session over SSE, QR code, reboot/shutdown buttons. | `sudo bash start.sh` or `setup/cockpit.service` |
| `projects/phone-input` | 5000 | Phone as mouse/keyboard/touchpad (uinput) with a YouTube tab (`yt-dlp`); auto-starts Claude Code in tmux (`setup:claude`, 60×30). | `sudo bash start.sh` or `setup/phone-server.service` |
| `projects/pegasus-pad` | 5001 | Gamepad companion for Pegasus Frontend: injects keys via `xdotool` with PEGASUS and GAME (RetroArch) key maps. | `sudo bash start.sh` |

## Other pieces

- `mock_server.py` — runs all three UIs on a dev machine (localhost:5000) with fake auto-cycling Claude states; no uinput/Linux needed. `pip install flask flask-sock pillow`, then `python mock_server.py`.
- `gamepad/` — phone gamepad web app (`pad.html` + `server.py`) via uinput.
- `claude-session.sh` — launch/reattach Claude Code in the fixed tmux session `setup:claude`.
- `copy_key.py` — Windows helper that pushes your public key to the Pi over SSH (paramiko).
- `examples/` — `blink.py`, `generative_art.py`, `midi_player.py`, `neopixel_rainbow.py`.
- `config/` — `config.txt.additions` (/boot/config.txt snippets), `phone-ui-rules.md`, `claude-skills/` (slash-command skills installed by `setup/install-skills.sh`).

## Setup

On the Pi (Raspberry Pi OS Bookworm):

```bash
bash setup/base.sh            # system update + essential tools
bash setup/remote-access.sh   # SSH hardening + Tailscale
bash setup/claude-code.sh     # install Claude Code CLI
bash setup/install-skills.sh  # install slash-command skills
# optional: bash setup/audio.sh, led.sh, media.sh, visual.sh,
#           retroarch.sh, phone-input.sh, phone-gamepad.sh
```

Start a project:

```bash
cd projects/cockpit && sudo bash start.sh
```

Or register as a service: copy `setup/cockpit.service` (or `phone-server.service`) to `/etc/systemd/system/` and run `systemctl enable --now cockpit.service`.

## Notes

- 1 GB RAM: no PyTorch/TensorFlow full (use `tflite-runtime`), `make -j2` max, pygame at 720p/30fps is comfortable.
- Scripts that touch GPIO/uinput need sudo; prefer `gpiozero` over `RPi.GPIO`.
- Install Python packages with `pip3 install --break-system-packages <pkg>`.
- The projects are also referenced from a USB mount (`/media/peepo/KINGSTON/PI3`); the systemd units wait for that mount before starting.
