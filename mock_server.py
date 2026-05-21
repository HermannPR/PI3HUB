#!/usr/bin/env python3
"""Mock Pi server for local UI dev — no uinput/Linux required.
pip install flask flask-sock pillow
python mock_server.py  →  http://localhost:5000
"""
from flask import Flask, jsonify, send_from_directory, Response, stream_with_context, request
from flask_sock import Sock
import json, time, os, io, threading

STATIC = os.path.join(os.path.dirname(__file__), "projects/phone-input/static")
app = Flask(__name__, static_folder=STATIC)
sock = Sock(app)

# ── Fake Claude states (cycles automatically) ──────────────────────────────
CYCLES = [
    {
        "mode": "idle", "duration": 5,
        "preview": [
            "peepo@PI:~ $ claude",
            "Claude Code v2.1.146",
            "Welcome back Hermann!",
            "Run /init to create a CLAUDE.md file",
            "Note: launched in home directory",
            "❯ Try \"refactor <filepath>\"",
            "⏵⏵ bypass permissions on (shift+tab to cycle) · ← for agents",
            "                                          ● high · /effort",
        ],
        "options": [], "yesno": False,
    },
    {
        "mode": "thinking", "duration": 6,
        "preview": [
            "peepo@PI:~ $ claude",
            "❯ what files are in the phone-input project?",
            "● Bash(ls -la /media/peepo/KINGSTON/PI3/projects/phone-input/)",
            "⎿  total 48",
            "   -rw-r--r-- 1 peepo peepo 18432 May 21 server.py",
            "   -rw-r--r-- 1 peepo peepo   892 May 21 start.sh",
            "   drwxr-xr-x 2 peepo peepo  4096 May 21 static/",
            "● Bash(cat /media/peepo/KINGSTON/PI3/projects/phone-input/start.sh)",
            "⎿  #!/usr/bin/env bash",
            "   modprobe uinput 2>/dev/null || true",
            "✻ Analyzing… 4s",
            "⏵⏵ esc to interrupt",
        ],
        "options": [], "yesno": False,
    },
    {
        "mode": "options", "duration": 7,
        "preview": [
            "❯ what files are in the phone-input project?",
            "",
            "Found these files:",
            "  server.py — Flask server, mouse/keyboard via uinput",
            "  start.sh  — startup, creates tmux session, runs server",
            "  static/index.html — phone UI wrapper",
            "",
            "What next?",
            "",
            "❯ 1. Show server.py",
            "  2. Edit index.html",
            "  3. Check git log",
            "  4. Run git pull",
        ],
        "options": [
            {"num": "1", "label": "Show server.py"},
            {"num": "2", "label": "Edit index.html"},
            {"num": "3", "label": "Check git log"},
            {"num": "4", "label": "Run git pull"},
        ],
        "yesno": False,
    },
    {
        "mode": "yesno", "duration": 5,
        "preview": [
            "I'll update start.sh to add a deploy alias.",
            "Changes:",
            "  • projects/phone-input/start.sh",
            "",
            "This will add `alias deploy` to the session.",
            "Proceed? [y/n]",
        ],
        "options": [], "yesno": True,
    },
    {
        "mode": "thinking", "duration": 4,
        "preview": [
            "✓ YES",
            "● Edit(start.sh)",
            "⎿  Updated start.sh",
            "● Bash(sudo systemctl restart phone-server)",
            "⎿  (no output)",
            "⠙ Verifying… 2s",
        ],
        "options": [], "yesno": False,
    },
    {
        "mode": "idle", "duration": 5,
        "preview": [
            "✔ Done. Alias added and server restarted.",
            "",
            "Run `deploy` in any shell to pull + restart.",
            "",
            "❯ ",
            "⏵⏵ bypass permissions on (shift+tab to cycle) · ← for agents",
        ],
        "options": [], "yesno": False,
    },
]

_idx = 0
_lock = threading.Lock()

def _cycle():
    global _idx
    while True:
        with _lock:
            dur = CYCLES[_idx % len(CYCLES)]["duration"]
        time.sleep(dur)
        with _lock:
            _idx += 1

threading.Thread(target=_cycle, daemon=True).start()

def current():
    with _lock:
        return dict(CYCLES[_idx % len(CYCLES)])

# ── Routes ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(STATIC, "index.html")

@app.route("/claude-state")
def claude_state():
    def gen():
        last = None
        while True:
            s = current()
            out = {k: s[k] for k in ("mode", "preview", "options", "yesno")}
            if out != last:
                yield f"data: {json.dumps(out)}\n\n"
                last = out
            else:
                yield ": ping\n\n"
            time.sleep(0.6)
    return Response(stream_with_context(gen()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/screen-info")
def screen_info():
    return jsonify(w=1920, h=1080)

@app.route("/screen-stream")
def screen_stream():
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (960, 540), (10, 20, 10))
        d = ImageDraw.Draw(img)
        d.text((40, 240), "[ PI SCREEN MOCK ]", fill=(0, 100, 40))
        d.text((40, 270), "Real stream needs Pi connection", fill=(0, 60, 25))
        buf = io.BytesIO(); img.save(buf, "JPEG", quality=70); frame = buf.getvalue()
    except Exception:
        frame = b""
    def gen():
        while True:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            time.sleep(1)
    return Response(stream_with_context(gen()),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/audio-stream")
def audio_stream():
    # Minimal valid MP3 silence frame
    frame = bytes([0xFF,0xFB,0x90,0x00]+[0x00]*413)
    def gen():
        while True:
            yield frame; time.sleep(0.1)
    return Response(stream_with_context(gen()), mimetype="audio/mpeg",
                    headers={"Cache-Control": "no-cache"})

# All write endpoints — just ack
_ok = {"ok": True, "enabled": True, "vol": 80, "chars": 0}
for _p in ["/mouse","/key","/text","/prompt","/choose",
           "/screen-toggle","/screen-input","/audio-volume","/claude-restart"]:
    app.add_url_rule(_p, "mock"+_p.replace("/","_"),
                     lambda: jsonify(**_ok), methods=["POST"])

@sock.route("/ws")
def ws_mock(ws):
    while True:
        try: ws.receive()
        except Exception: break

if __name__ == "__main__":
    print("\n  Mock Pi server — UI dev mode")
    print("  Open: http://localhost:5000\n")
    print("  States cycle: idle -> thinking -> options -> yesno -> ...\n")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
