# Retro Gaming Helper

RetroArch / libretro helper for Raspberry Pi 3.

Usage: `/retro [system]` — e.g. `/retro nes`, `/retro n64`

For the given system (or general if no arg), provide:
- Correct core name and path for this Pi (`~/.config/retroarch/cores/`)
- ROM directory on Kingston: `/media/peepo/Kingston/roms/<system>/`
- Launch command: `retroarch -L <core> <rom>`
- Known Pi 3 performance tips for that system (resolution, frame skip, audio driver)

Supported: nes (nestopia), snes (snes9x), gba (mgba), gbc (gambatte), genesis (genesisplusgx), ps1 (pcsx_rearmed), n64 (parallel_n64), nds (desmume)

$ARGUMENTS
