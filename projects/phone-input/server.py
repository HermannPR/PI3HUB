#!/usr/bin/env python3
"""Phone → Pi mouse + keyboard server. Run with sudo."""
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_sock import Sock
import uinput
import os
import sys
import re
import json
import subprocess
import time
import threading
import io
from PIL import Image

if os.geteuid() != 0:
    sys.exit("Run with sudo: sudo python3 server.py")

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

# char → (uinput_key, needs_shift)
CHAR_MAP = {
    'a':(uinput.KEY_A,False),'b':(uinput.KEY_B,False),'c':(uinput.KEY_C,False),
    'd':(uinput.KEY_D,False),'e':(uinput.KEY_E,False),'f':(uinput.KEY_F,False),
    'g':(uinput.KEY_G,False),'h':(uinput.KEY_H,False),'i':(uinput.KEY_I,False),
    'j':(uinput.KEY_J,False),'k':(uinput.KEY_K,False),'l':(uinput.KEY_L,False),
    'm':(uinput.KEY_M,False),'n':(uinput.KEY_N,False),'o':(uinput.KEY_O,False),
    'p':(uinput.KEY_P,False),'q':(uinput.KEY_Q,False),'r':(uinput.KEY_R,False),
    's':(uinput.KEY_S,False),'t':(uinput.KEY_T,False),'u':(uinput.KEY_U,False),
    'v':(uinput.KEY_V,False),'w':(uinput.KEY_W,False),'x':(uinput.KEY_X,False),
    'y':(uinput.KEY_Y,False),'z':(uinput.KEY_Z,False),
    'A':(uinput.KEY_A,True),'B':(uinput.KEY_B,True),'C':(uinput.KEY_C,True),
    'D':(uinput.KEY_D,True),'E':(uinput.KEY_E,True),'F':(uinput.KEY_F,True),
    'G':(uinput.KEY_G,True),'H':(uinput.KEY_H,True),'I':(uinput.KEY_I,True),
    'J':(uinput.KEY_J,True),'K':(uinput.KEY_K,True),'L':(uinput.KEY_L,True),
    'M':(uinput.KEY_M,True),'N':(uinput.KEY_N,True),'O':(uinput.KEY_O,True),
    'P':(uinput.KEY_P,True),'Q':(uinput.KEY_Q,True),'R':(uinput.KEY_R,True),
    'S':(uinput.KEY_S,True),'T':(uinput.KEY_T,True),'U':(uinput.KEY_U,True),
    'V':(uinput.KEY_V,True),'W':(uinput.KEY_W,True),'X':(uinput.KEY_X,True),
    'Y':(uinput.KEY_Y,True),'Z':(uinput.KEY_Z,True),
    '0':(uinput.KEY_0,False),'1':(uinput.KEY_1,False),'2':(uinput.KEY_2,False),
    '3':(uinput.KEY_3,False),'4':(uinput.KEY_4,False),'5':(uinput.KEY_5,False),
    '6':(uinput.KEY_6,False),'7':(uinput.KEY_7,False),'8':(uinput.KEY_8,False),
    '9':(uinput.KEY_9,False),
    '!':(uinput.KEY_1,True),'@':(uinput.KEY_2,True),'#':(uinput.KEY_3,True),
    '$':(uinput.KEY_4,True),'%':(uinput.KEY_5,True),'^':(uinput.KEY_6,True),
    '&':(uinput.KEY_7,True),'*':(uinput.KEY_8,True),'(':(uinput.KEY_9,True),
    ')':(uinput.KEY_0,True),
    ' ':(uinput.KEY_SPACE,False),'\n':(uinput.KEY_ENTER,False),'\t':(uinput.KEY_TAB,False),
    '-':(uinput.KEY_MINUS,False),'_':(uinput.KEY_MINUS,True),
    '=':(uinput.KEY_EQUAL,False),'+':(uinput.KEY_EQUAL,True),
    '[':(uinput.KEY_LEFTBRACE,False),'{':(uinput.KEY_LEFTBRACE,True),
    ']':(uinput.KEY_RIGHTBRACE,False),'}':(uinput.KEY_RIGHTBRACE,True),
    ';':(uinput.KEY_SEMICOLON,False),':':(uinput.KEY_SEMICOLON,True),
    "'":(uinput.KEY_APOSTROPHE,False),'"':(uinput.KEY_APOSTROPHE,True),
    ',':(uinput.KEY_COMMA,False),'<':(uinput.KEY_COMMA,True),
    '.':(uinput.KEY_DOT,False),'>':(uinput.KEY_DOT,True),
    '/':(uinput.KEY_SLASH,False),'?':(uinput.KEY_SLASH,True),
    '\\':(uinput.KEY_BACKSLASH,False),'|':(uinput.KEY_BACKSLASH,True),
    '`':(uinput.KEY_GRAVE,False),'~':(uinput.KEY_GRAVE,True),
}

ANSI_RE   = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
# Box-drawing, block elements, braille (Claude Code TUI chrome)
JUNK_RE   = re.compile(r'[─-▟▀-▟⠀-⣿⬀-⯿]')

device = uinput.Device(ALL_KEYS, name="phone-input")
app = Flask(__name__, static_folder="static")
sock = Sock(app)
STATIC = os.path.join(os.path.dirname(__file__), "static")

TMUX_SESSION = "setup"
TMUX_WINDOW  = "claude"
TMUX_SOCKET  = "/tmp/tmux-1000/default"   # peepo uid=1000; server runs as root


def tmux(*args):
    """Run tmux command against peepo's socket (server runs as root)."""
    return subprocess.run(
        ["tmux", "-S", TMUX_SOCKET] + list(args),
        capture_output=True, text=True, timeout=5
    )


def type_text(txt):
    """Type a string via uinput — same path as keyboard tab, works on focused window."""
    for ch in txt:
        if ch not in CHAR_MAP:
            continue
        code, shift = CHAR_MAP[ch]
        if shift:
            device.emit(uinput.KEY_LEFTSHIFT, 1, syn=False)
        device.emit(code, 1, syn=False)
        device.emit(code, 0, syn=False)
        if shift:
            device.emit(uinput.KEY_LEFTSHIFT, 0, syn=False)
        device.syn()
        time.sleep(0.012)


@sock.route("/ws")
def ws_mouse(ws):
    """WebSocket — low-latency mouse movement. Falls back to HTTP /mouse for clicks/scroll."""
    while True:
        try:
            data = json.loads(ws.receive())
        except Exception:
            break
        dx = int(data.get("dx", 0))
        dy = int(data.get("dy", 0))
        scroll = int(data.get("scroll", 0))
        btn = data.get("btn")
        action = data.get("action", "click")
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
    action = d.get("action", "tap")

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
    """Type text into focused window via uinput."""
    d = request.get_json()
    txt = d.get("text", "")
    if not txt:
        return jsonify(ok=False)
    type_text(txt)
    return jsonify(ok=True, chars=len(txt))


@app.route("/prompt", methods=["POST"])
def prompt():
    """Send prompt text directly to Claude Code tmux pane."""
    d = request.get_json()
    txt = d.get("text", "")
    if not txt:
        return jsonify(ok=False)
    target = f"{TMUX_SESSION}:{TMUX_WINDOW}"
    tmux("send-keys", "-t", target, "-l", txt)
    tmux("send-keys", "-t", target, "Enter")
    return jsonify(ok=True, chars=len(txt))


def read_tmux():
    try:
        r = tmux("capture-pane", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}", "-p", "-S", "-300")
        raw = ANSI_RE.sub("", r.stdout)
        lines = []
        for line in raw.splitlines():
            cleaned = JUNK_RE.sub("", line).strip()
            if len(cleaned) > 1:
                lines.append(cleaned)
        return "\n".join(lines)
    except Exception:
        return ""


def parse_claude_state(raw):
    lines  = [l for l in raw.splitlines() if l.strip()]
    tail   = lines[-30:] if len(lines) > 30 else lines
    screen = tail[-20:]   # scan more lines — options may follow long Claude output

    state = {
        "mode":    "idle",
        "preview": tail[-80:],
        "options": [],
        "yesno":   False,
    }

    screen_joined = "\n".join(screen)

    # Thinking — check bottom 10 lines only
    bottom = "\n".join(screen[-10:])
    is_thinking = bool(
        re.search(r"esc to interrupt|ctrl.c to interrupt", bottom, re.I) or
        re.search(r"[✻✢·]\s.*\d+s", bottom) or
        re.search(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]\s", bottom)
    )
    if is_thinking:
        state["mode"] = "thinking"

    # Options — scan last 20 lines, collect all numbered items
    opts = []
    seen_nums = set()
    for line in screen:
        m = re.match(r"[\s❯>]*(\d+)[.)]\s+(.+)", line)
        if m and m.group(1) not in seen_nums:
            seen_nums.add(m.group(1))
            opts.append({"num": m.group(1), "label": m.group(2).strip()[:40]})
    has_cursor = any("❯" in l or bool(re.match(r"\s*>\s*\d", l)) for l in screen)
    if opts and (len(opts) >= 2 or has_cursor) and not is_thinking:
        state["mode"]    = "options"
        state["options"] = opts[:6]

    # Yes/No
    if re.search(r"\[y/n\]|\[Y/n\]|\[yes/no\]", screen_joined, re.I) and not is_thinking:
        state["mode"]  = "yesno"
        state["yesno"] = True

    return state


@app.route("/claude-state")
def claude_state():
    def generate():
        last = None
        while True:
            raw   = read_tmux()
            state = parse_claude_state(raw)
            if state != last:
                yield f"data: {json.dumps(state)}\n\n"
                last = state
            else:
                yield ": ping\n\n"
            time.sleep(0.6)
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.route("/choose", methods=["POST"])
def choose():
    """Send a choice to the Claude Code tmux pane."""
    d      = request.get_json()
    choice = d.get("choice", "")
    self_complete = {"esc", "ctrl-c", "ctrl-z", "enter"}
    special = {
        "esc":    "Escape",
        "ctrl-c": "C-c",
        "ctrl-z": "C-z",
        "enter":  "Enter",
    }
    key = special.get(choice.lower(), choice)
    args = ["send-keys", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}", key]
    if choice.lower() not in self_complete:
        args.append("Enter")
    tmux(*args)
    return jsonify(ok=True)


# ── Screen capture ────────────────────────────────────────────────────────────
SCREEN_W   = 960
SCREEN_H   = 540
SCREEN_FPS = 2
SCREEN_Q   = 60
PI_W, PI_H = 1920, 1080  # updated on first capture

_screen_lock    = threading.Lock()
_screen_frame   = b""
_screen_enabled = False          # OFF by default; toggled via /screen-toggle
_screen_res     = [1920, 1080]
_XAUTH_GLOB     = "/tmp/serverauth.*"


def _find_xauth():
    import glob
    files = glob.glob(_XAUTH_GLOB)
    return files[0] if files else "/home/peepo/.Xauthority"


def _capture_loop():
    global _screen_frame, PI_W, PI_H
    interval = 1.0 / SCREEN_FPS
    while _screen_enabled:
        t0 = time.time()
        try:
            xauth = _find_xauth()
            r = subprocess.run(
                ["sudo", "-u", "peepo",
                 "env", f"DISPLAY=:0", f"XAUTHORITY={xauth}",
                 "scrot", "-"],
                capture_output=True, timeout=5
            )
            if r.returncode == 0 and r.stdout:
                img = Image.open(io.BytesIO(r.stdout))
                PI_W, PI_H = img.size
                _screen_res[0], _screen_res[1] = img.size
                img = img.resize((SCREEN_W, SCREEN_H), Image.BILINEAR)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=SCREEN_Q)
                with _screen_lock:
                    _screen_frame = buf.getvalue()
        except Exception:
            pass
        time.sleep(max(0, interval - (time.time() - t0)))
    with _screen_lock:
        _screen_frame = b""


@app.route("/screen-toggle", methods=["POST"])
def screen_toggle():
    global _screen_enabled
    _screen_enabled = not _screen_enabled
    if _screen_enabled:
        threading.Thread(target=_capture_loop, daemon=True).start()
    return jsonify(ok=True, enabled=_screen_enabled)


@app.route("/screen-stream")
def screen_stream():
    if not _screen_enabled:
        return Response("disabled", status=503)

    def generate():
        try:
            last = None
            while _screen_enabled:
                with _screen_lock:
                    frame = _screen_frame
                if frame and frame is not last:
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                           + frame + b"\r\n")
                    last = frame
                time.sleep(0.08)
        except GeneratorExit:
            pass

    return Response(stream_with_context(generate()),
                    mimetype="multipart/x-mixed-replace; boundary=frame",
                    headers={"Cache-Control": "no-cache"})


@app.route("/screen-info")
def screen_info():
    return jsonify(w=_screen_res[0], h=_screen_res[1])


@app.route("/screen-input", methods=["POST"])
def screen_input():
    d      = request.get_json()
    x      = int(d.get("x", 0))
    y      = int(d.get("y", 0))
    kind   = d.get("type", "click")
    scroll = int(d.get("scroll", 0))
    xauth  = _find_xauth()
    xenv   = {"DISPLAY": ":0", "XAUTHORITY": xauth}

    if kind == "move":
        subprocess.run(["xdotool", "mousemove", str(x), str(y)], env=xenv)
    elif kind == "click":
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], env=xenv)
    elif kind == "rightclick":
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "3"], env=xenv)
    elif kind == "down":
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "mousedown", "1"], env=xenv)
    elif kind == "up":
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "mouseup", "1"], env=xenv)
    elif kind == "scroll":
        btn = "4" if scroll > 0 else "5"
        for _ in range(abs(scroll)):
            subprocess.run(["xdotool", "click", btn], env=xenv)
    return jsonify(ok=True)


# ── Audio stream ──────────────────────────────────────────────────────────────
_PW_ENV = {
    "HOME": "/home/peepo",
    "XDG_RUNTIME_DIR": "/run/user/1000",
    "PIPEWIRE_RUNTIME_DIR": "/run/user/1000",
}
# Default Pi headphone output — fallback if detection fails
_DEFAULT_SINK = "alsa_output.platform-3f00b840.mailbox.stereo-fallback"


@app.route("/audio-stream")
def audio_stream():
    def generate():
        # Must set PipeWire env inside bash -c: sudo resets env, stripping XDG_RUNTIME_DIR
        pw_cmd = (
            "XDG_RUNTIME_DIR=/run/user/1000 PIPEWIRE_RUNTIME_DIR=/run/user/1000 "
            f"pw-record --target '{_DEFAULT_SINK}' --rate 44100 --channels 2 -"
        )
        # pw-record outputs 24-byte LE-AU header then raw s16le PCM
        pw = subprocess.Popen(
            ["sudo", "-u", "peepo", "bash", "-c", pw_cmd],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            bufsize=0
        )
        ff = subprocess.Popen(
            ["ffmpeg", "-loglevel", "quiet",
             "-f", "s16le", "-ar", "44100", "-ac", "2", "-i", "pipe:0",
             "-acodec", "libmp3lame", "-ab", "96k", "-ar", "44100",
             "-f", "mp3", "pipe:1"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        # Pump thread: skip 24-byte header, forward rest to ffmpeg stdin
        def _pump():
            try:
                remaining = 24
                while remaining > 0:
                    d = pw.stdout.read(remaining)
                    if not d:
                        break
                    remaining -= len(d)
                while True:
                    d = pw.stdout.read(4096)
                    if not d:
                        break
                    ff.stdin.write(d)
                    ff.stdin.flush()
            except Exception:
                pass
            finally:
                try: ff.stdin.close()
                except Exception: pass
        threading.Thread(target=_pump, daemon=True).start()
        try:
            while True:
                chunk = ff.stdout.read1(8192)  # read1: returns what's available, no blocking for full buffer
                if not chunk:
                    break
                yield chunk
        finally:
            ff.kill(); pw.kill()
            ff.wait(); pw.wait()

    return Response(
        stream_with_context(generate()),
        mimetype="audio/mpeg",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.route("/audio-volume", methods=["POST"])
def audio_volume():
    vol = int(request.get_json().get("vol", 80))
    vol = max(0, min(100, vol))
    subprocess.run(
        ["sudo", "-u", "peepo", "wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{vol}%"],
        env=_PW_ENV, timeout=3
    )
    return jsonify(ok=True, vol=vol)


@app.route("/claude-restart", methods=["POST"])
def claude_restart():
    target = f"{TMUX_SESSION}:{TMUX_WINDOW}"
    tmux("send-keys", "-t", target, "C-c")
    time.sleep(0.4)
    tmux("send-keys", "-t", target, "q", "Enter")
    time.sleep(0.4)
    tmux("send-keys", "-t", target, "claude", "Enter")
    threading.Thread(target=_watch_trust, daemon=True).start()
    return jsonify(ok=True)


def _watch_trust():
    """Poll tmux pane for Claude trust prompt and accept it."""
    target = f"{TMUX_SESSION}:{TMUX_WINDOW}"
    for _ in range(40):
        time.sleep(1)
        raw = read_tmux()
        if re.search(r"trust this folder|Enter to confirm", raw, re.I):
            tmux("send-keys", "-t", target, "", "Enter")
            return
        if "❯" in raw and "Try " in raw:
            return  # already at idle prompt


threading.Thread(target=_watch_trust, daemon=True).start()


if __name__ == "__main__":
    ip = os.popen("hostname -I").read().split()[0]
    print(f"Phone Input Server running.")
    print(f"Open on phone: http://{ip}:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)
