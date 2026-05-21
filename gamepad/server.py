#!/usr/bin/env python3
"""Phone gamepad server — receives button presses, injects via uinput."""
from flask import Flask, request, jsonify, send_from_directory
import uinput
import os

BUTTONS = {
    "up":     uinput.KEY_UP,
    "down":   uinput.KEY_DOWN,
    "left":   uinput.KEY_LEFT,
    "right":  uinput.KEY_RIGHT,
    "a":      uinput.KEY_X,
    "b":      uinput.KEY_Z,
    "x":      uinput.KEY_S,
    "y":      uinput.KEY_A,
    "l":      uinput.KEY_Q,
    "r":      uinput.KEY_W,
    "start":  uinput.KEY_ENTER,
    "select": uinput.KEY_RIGHTSHIFT,
}

device = uinput.Device(list(BUTTONS.values()))
app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "pad.html")


@app.route("/press", methods=["POST"])
def press():
    data = request.get_json()
    btn = data.get("button", "")
    action = data.get("action", "down")  # "down" or "up"
    if btn in BUTTONS:
        key = BUTTONS[btn]
        device.emit(key, 1 if action == "down" else 0)
    return jsonify(ok=True)


if __name__ == "__main__":
    print("Gamepad server running.")
    print(f"Open on phone: http://<pi-ip>:5000")
    app.run(host="0.0.0.0", port=5000)
