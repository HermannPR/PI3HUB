# Pi Status

Show current Raspberry Pi 3 hardware status.

Run these commands and report results concisely:
- `vcgencmd measure_temp` — CPU temp
- `vcgencmd get_throttled` — thermal/undervoltage flags (0x0 = good)
- `free -h` — RAM usage
- `df -h /media/peepo/Kingston` — Kingston USB drive space
- `tmux list-sessions` — active tmux sessions

Flag any issues: temp >70°C, throttled ≠ 0x0, RAM >800MB used.

$ARGUMENTS
