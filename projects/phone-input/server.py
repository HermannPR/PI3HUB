#!/usr/bin/env python3
"""Phone → Pi mouse + keyboard server. Run with sudo."""
from flask import Flask, request, jsonify, send_from_directory
import uinput
import os
import sys

if os.geteuid() != 0:
    sys.exit("Run with sudo: sudo python3 server.py")

# All keys we expose to the keyboard UI
ALL_KEYS = [
    uinput.KEY_A, uinput.KEY_B, uinput.KEY_C, uinput.KEY_D, uinput.KEY_E,
    uinput.KEY_F, uinput.KEY_G, uinput.KEY_H, uinput.KEY_I, uinput.KEY_J,
    uinput.KEY_K, uinput.KEY_L, uinput.KEY_M, uinput.KEY_N, uinput.KEY_O,
    uinput.KEY_P, uinput.KEY_Q, uinput.KEY_R, uinput.KEY_S, uinput.KEY_T,
    uinput.KEY_U, uinput.KEY_V, uinput.KEY_W, uinput.KEY_X, uinput.KEY_Y,
    uinput.KEY_Z,
    uinput.KEY_0, uinput.KEY_1, uinput.KEY_2, uinput.KEY_3, uinput.KEY_4,
    uinput.KEY_5, uinput.KEY_6, uinput.KEY_7, uinput.KEY_8, uinput.KEY_9,
    uinput.KEY_SPACE, uinput.KEY_ENTER, uinput.KEY_BACKSPACE, uinput.KEY_TAB,
    uinput.KEY_ESC, uinput.KEY_LEFTSHIFT, uinput.KEY_RIGHTSHIFT,
    uinput.KEY_LEFTCTRL, uinput.KEY_LEFTALT,
    uinput.KEY_UP, uinput.KEY_DOWN, uinput.KEY_LEFT, uinput.KEY_RIGHT,
    uinput.KEY_HOME, uinput.KEY_END, uinput.KEY_DELETE,
    uinput.KEY_MINUS, uinput.KEY_EQUAL, uinput.KEY_LEFTBRACE,
    uinput.KEY_RIGHTBRACE, uinput.KEY_SEMICOLON, uinput.KEY_APOSTROPHE,
    uinput.KEY_COMMA, uinput.KEY_DOT, uinput.KEY_SLASH, uinput.KEY_BACKSLASH,
    uinput.KEY_GRAVE,
    # Mouse
    uinput.REL_X, uinput.REL_Y, uinput.REL_WHEEL,
    uinput.BTN_LEFT, uinput.BTN_RIGHT, uinput.BTN_MIDDLE,
]

KEY_MAP = {
    "a": uinput.KEY_A, "b": uinput.KEY_B, "c": uinput.KEY_C,
    "d": uinput.KEY_D, "e": uinput.KEY_E, "f": uinput.KEY_F,
    "g": uinput.KEY_G, "h": uinput.KEY_H, "i": uinput.KEY_I,
    "j": uinput.KEY_J, "k": uinput.KEY_K, "l": uinput.KEY_L,
    "m": uinput.KEY_M, "n": uinput.KEY_N, "o": uinput.KEY_O,
    "p": uinput.KEY_P, "q": uinput.KEY_Q, "r": uinput.KEY_R,
    "s": uinput.KEY_S, "t": uinput.KEY_T, "u": uinput.KEY_U,
    "v": uinput.KEY_V, "w": uinput.KEY_W, "x": uinput.KEY_X,
    "y": uinput.KEY_Y, "z": uinput.KEY_Z,
    "0": uinput.KEY_0, "1": uinput.KEY_1, "2": uinput.KEY_2,
    "3": uinput.KEY_3, "4": uinput.KEY_4, "5": uinput.KEY_5,
    "6": uinput.KEY_6, "7": uinput.KEY_7, "8": uinput.KEY_8,
    "9": uinput.KEY_9,
    " ": uinput.KEY_SPACE, "enter": uinput.KEY_ENTER,
    "backspace": uinput.KEY_BACKSPACE, "tab": uinput.KEY_TAB,
    "esc": uinput.KEY_ESC, "shift": uinput.KEY_LEFTSHIFT,
    "ctrl": uinput.KEY_LEFTCTRL, "alt": uinput.KEY_LEFTALT,
    "up": uinput.KEY_UP, "down": uinput.KEY_DOWN,
    "left": uinput.KEY_LEFT, "right": uinput.KEY_RIGHT,
    "home": uinput.KEY_HOME, "end": uinput.KEY_END,
    "delete": uinput.KEY_DELETE,
    "-": uinput.KEY_MINUS, "=": uinput.KEY_EQUAL,
    "[": uinput.KEY_LEFTBRACE, "]": uinput.KEY_RIGHTBRACE,
    ";": uinput.KEY_SEMICOLON, "'": uinput.KEY_APOSTROPHE,
    ",": uinput.KEY_COMMA, ".": uinput.KEY_DOT,
    "/": uinput.KEY_SLASH, "\\": uinput.KEY_BACKSLASH,
    "`": uinput.KEY_GRAVE,
}

device = uinput.Device(ALL_KEYS, name="phone-input")
app = Flask(__name__, static_folder="static")
STATIC = os.path.join(os.path.dirname(__file__), "static")


@app.route("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.route("/mouse", methods=["POST"])
def mouse():
    d = request.get_json()
    dx = int(d.get("dx", 0))
    dy = int(d.get("dy", 0))
    scroll = int(d.get("scroll", 0))
    btn = d.get("btn")
    action = d.get("action", "click")

    if dx or dy:
        device.emit(uinput.REL_X, dx, syn=False)
        device.emit(uinput.REL_Y, dy)
    if scroll:
        device.emit(uinput.REL_WHEEL, scroll)
    if btn == "left":
        device.emit(uinput.BTN_LEFT, 1 if action == "down" else 0)
    elif btn == "right":
        device.emit(uinput.BTN_RIGHT, 1 if action == "down" else 0)
    elif btn == "click":
        device.emit(uinput.BTN_LEFT, 1, syn=False)
        device.emit(uinput.BTN_LEFT, 0)
    elif btn == "rightclick":
        device.emit(uinput.BTN_RIGHT, 1, syn=False)
        device.emit(uinput.BTN_RIGHT, 0)
    return jsonify(ok=True)


@app.route("/key", methods=["POST"])
def key():
    d = request.get_json()
    k = d.get("key", "").lower()
    action = d.get("action", "tap")  # tap | down | up

    if k not in KEY_MAP:
        return jsonify(ok=False, err="unknown key")

    code = KEY_MAP[k]
    if action == "tap":
        device.emit(code, 1, syn=False)
        device.emit(code, 0)
    elif action == "down":
        device.emit(code, 1)
    elif action == "up":
        device.emit(code, 0)
    return jsonify(ok=True)


@app.route("/text", methods=["POST"])
def text():
    import subprocess
    d = request.get_json()
    txt = d.get("text", "")
    if not txt:
        return jsonify(ok=False)
    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    env["XAUTHORITY"] = "/home/peepo/.Xauthority"
    subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "20", "--", txt], env=env)
    return jsonify(ok=True, chars=len(txt))


@app.route("/prompt", methods=["POST"])
def prompt():
    import subprocess
    d = request.get_json()
    txt = d.get("text", "")
    if not txt:
        return jsonify(ok=False)
    env = os.environ.copy()
    env["DISPLAY"] = ":0"
    env["XAUTHORITY"] = "/home/peepo/.Xauthority"
    subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "20", "--", txt], env=env)
    subprocess.run(["xdotool", "key", "Return"], env=env)
    return jsonify(ok=True, chars=len(txt))


if __name__ == "__main__":
    ip = os.popen("hostname -I").read().split()[0]
    print(f"Phone Input Server running.")
    print(f"Open on phone: http://{ip}:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)
