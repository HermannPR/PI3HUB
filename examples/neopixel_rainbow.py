#!/usr/bin/env python3
"""Rainbow cycle on WS281x/NeoPixel strip. Requires: sudo python3."""
import time
import board
import neopixel

LED_COUNT = 30          # number of pixels in your strip
LED_PIN = board.D18     # GPIO 18 (PWM)
BRIGHTNESS = 0.3        # 0.0–1.0

pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)


def wheel(pos):
    """Color wheel: pos 0-255 -> RGB tuple."""
    pos = pos % 255
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)


print("Rainbow cycle. Ctrl+C to stop.")
try:
    step = 0
    while True:
        for i in range(LED_COUNT):
            pixels[i] = wheel((i * 256 // LED_COUNT + step) & 255)
        pixels.show()
        step = (step + 1) % 256
        time.sleep(0.02)
finally:
    pixels.fill((0, 0, 0))
    pixels.show()
