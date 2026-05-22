#!/usr/bin/env python3
"""
Pegasus Frontend gamepad companion — port 5001.
Injects keyboard input via xdotool into the Pi X session.
Run: sudo python3 server.py   (or via start.sh)
"""
from flask import Flask, jsonify, send_from_directory, request
import os, subprocess, glob, socket, threading, time

PORT   = 5001
STATIC = os.path.join(os.path.dirname(__file__), "static")
app    = Flask(__name__, static_folder=STATIC)

# ── Key maps ──────────────────────────────────────────────────────────────────
# Pegasus Frontend default keyboard layout
PEGASUS = {
    "up":     "Up",       "down":  "Down",
    "left":   "Left",     "right": "Right",
    "a":      "Return",   "b":     "Escape",
    "x":      "F1",       "y":     "F2",
    "l1":     "Prior",    "r1":    "Next",      # PgUp/PgDn = prev/next page
    "l2":     "F6",       "r2":    "F5",        # prev/next collection
    "select": "BackSpace","start": "Return",    "home": "Escape",
}

# RetroArch default keyboard config
GAME = {
    "up":     "Up",       "down":  "Down",
    "left":   "Left",     "right": "Right",
    "a":      "x",        "b":     "z",
    "x":      "s",        "y":     "a",
    "l1":     "q",        "r1":    "w",
    "l2":     "e",        "r2":    "r",
    "select": "shift",    "start": "Return",    "home": "Escape",
}

# ── xdotool helper ────────────────────────────────────────────────────────────
_xauth_cache = None

def _find_xauth():
    global _xauth_cache
    if _xauth_cache:
        return _xauth_cache
    for pat in ["/tmp/serverauth.*", "/tmp/.serverauth.*",
                "/home/peepo/.Xauthority", "/root/.Xauthority"]:
        fs = glob.glob(pat)
        if fs:
            _xauth_cache = fs[0]
            return _xauth_cache
    return None

def xdo(action, key):
    env = {"DISPLAY": ":0"}
    xa  = _find_xauth()
    if xa:
        env["XAUTHORITY"] = xa
    cmd = {"press": "key", "down": "keydown", "up": "keyup"}.get(action, "key")
    try:
        subprocess.Popen(["xdotool", cmd, "--clearmodifiers", key],
                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print(f"[mock] xdotool {cmd} {key}")

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(STATIC, "index.html")

@app.route("/btn", methods=["POST"])
def btn():
    d      = request.get_json(force=True) or {}
    name   = d.get("btn", "")
    action = d.get("action", "press")   # press | down | up
    mode   = d.get("mode", "pegasus")
    km     = PEGASUS if mode == "pegasus" else GAME
    key    = km.get(name)
    if key:
        xdo(action, key)
    return jsonify(ok=True)

@app.route("/ping")
def ping():
    return jsonify(ok=True)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"

    url = f"http://{ip}:{PORT}"

    print()
    print("  ╔══════════════════════════════╗")
    print("  ║   PEGASUS GAMEPAD COMPANION  ║")
    print("  ╚══════════════════════════════╝")
    print()
    print(f"  Phone URL : {url}")
    print()

    # QR code via qrcode lib (optional)
    try:
        import qrcode as _qr
        qr = _qr.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        print()
    except ImportError:
        print("  (install qrcode for QR: pip3 install qrcode)")
        print()

    print("  Key maps:")
    print("    PEGASUS: arrows + Enter/Esc/F1/F2/PgUp/PgDn/F5/F6")
    print("    GAME   : RetroArch defaults (x/z/s/a/q/w/e/r)")
    print()
    print("  Ctrl+C to stop")
    print()

    app.run(host="0.0.0.0", port=PORT, threaded=True, debug=False)
