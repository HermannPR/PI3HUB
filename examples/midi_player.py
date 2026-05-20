#!/usr/bin/env python3
"""Simple MIDI event listener + FluidSynth playback. Requires jackd + fluidsynth running."""
import mido
import subprocess
import sys

SOUNDFONT = "/usr/share/sounds/sf2/FluidR3_GM.sf2"


def list_ports():
    print("Input ports:", mido.get_input_names())
    print("Output ports:", mido.get_output_names())


def play_file(path):
    subprocess.run(["fluidsynth", "-a", "alsa", "-m", "alsa_seq", "-i", SOUNDFONT, path])


def listen_live():
    ports = mido.get_input_names()
    if not ports:
        print("No MIDI input ports found.")
        sys.exit(1)
    port_name = ports[0]
    print(f"Listening on: {port_name}")
    with mido.open_input(port_name) as port:
        for msg in port:
            print(msg)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        play_file(sys.argv[1])
    else:
        list_ports()
        listen_live()
