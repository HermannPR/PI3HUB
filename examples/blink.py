#!/usr/bin/env python3
"""Blink GPIO 17 LED — smoke test for GPIO setup."""
from gpiozero import LED
from time import sleep

led = LED(17)

print("Blinking LED on GPIO 17. Ctrl+C to stop.")
while True:
    led.on()
    sleep(0.5)
    led.off()
    sleep(0.5)
