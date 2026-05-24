#!/usr/bin/env python3
"""
Pi Nexus — unified control server (port 5000).
Merges phone-input + pegasus-pad + nexus routes.
Run: sudo python3 server.py   (or via start.sh / cockpit.service)
"""
from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context
from flask_sock import Sock
import os, sys, re, json, subprocess, time, threading, io, glob, socket, shutil

if os.geteuid() != 0:
    sys.exit("Run with sudo: sudo python3 server.py")

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
STATIC       = os.path.join(BASE_DIR, "static")
PHONE_STATIC = os.path.join(BASE_DIR, "..", "phone-input", "static")
PAD_STATIC   = os.path.join(BASE_DIR, "..", "pegasus-pad",  "static")
GIT_DIR      = "/media/peepo/KINGSTON/PI3"
MODE_FILE    = "/etc/pi-mode"
TMP_MODE     = "/tmp/pi-mode"

TMUX_SOCK    = "/tmp/tmux-1000/default"
TMUX_SESSION = "setup"
TMUX_WINDOW  = "claude"
ANSI_RE      = re.compile(r"\x1b\[[0-9;]*[mKHFABCDJG]|\x1b\(B|\x1b=|\x1b>|\r")
JUNK_RE      = re.compile(
    "["
    r"^\x20-\x7e"
    "\u2500-\u259f"
    "\u2800-\u28ff"
    "\u2018\u2019"
    "\u201c\u201d"
    "\u2713\u2714\u2717\u2718"
    "\u273b\u2742\u2746"
    "\u25cf\u25aa\u25fb\u25fc"
    "\u276f\u27a1\u2728"
    "\u2600-\u26ff"
    "\u2b50"
    "\u23fa\u23fb\u23fc\u23f5"
    "\u00b0\u00b7\u00d7"
    "\u2190-\u2193"
    "\u2808\u2809\u2819\u2839\u2818\u2838"
    "\u283b\u2834\u2826\u2827\u2807\u280f"
    "\u256b\u2571\u2572\u253c\u2502\u2500"
    "\u251c\u2524\u252c\u2534"
    "\u2605\u2606\u2764"
    "\u25b6\u23f5"
    "]"
)

MODES = {
    "claude-dev": {"label": "CLAUDE DEV", "color": "#00e060", "ui": "/claude"},
    "gaming":     {"label": "GAMING",     "color": "#fd0",    "ui": "/gaming"},
    "desktop":    {"label": "DESKTOP",    "color": "#4af",    "ui": "/claude"},
    "headless":   {"label": "HEADLESS",   "color": "#888",    "ui": "/"},
}

# ── uinput ────────────────────────────────────────────────────────────────────
try:
    import uinput
    _ALL = [
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
        uinput.KEY_PAGEUP, uinput.KEY_PAGEDOWN,
        uinput.KEY_F1, uinput.KEY_F2, uinput.KEY_F3, uinput.KEY_F4,
        uinput.KEY_F5, uinput.KEY_F6,
        uinput.KEY_MINUS, uinput.KEY_EQUAL, uinput.KEY_LEFTBRACE,
        uinput.KEY_RIGHTBRACE, uinput.KEY_SEMICOLON, uinput.KEY_APOSTROPHE,
        uinput.KEY_COMMA, uinput.KEY_DOT, uinput.KEY_SLASH, uinput.KEY_BACKSLASH,
        uinput.KEY_GRAVE,
        uinput.REL_X, uinput.REL_Y, uinput.REL_WHEEL,
        uinput.BTN_LEFT, uinput.BTN_RIGHT, uinput.BTN_MIDDLE,
    ]
    KEY_MAP = {
        "a":uinput.KEY_A,"b":uinput.KEY_B,"c":uinput.KEY_C,"d":uinput.KEY_D,
        "e":uinput.KEY_E,"f":uinput.KEY_F,"g":uinput.KEY_G,"h":uinput.KEY_H,
        "i":uinput.KEY_I,"j":uinput.KEY_J,"k":uinput.KEY_K,"l":uinput.KEY_L,
        "m":uinput.KEY_M,"n":uinput.KEY_N,"o":uinput.KEY_O,"p":uinput.KEY_P,
        "q":uinput.KEY_Q,"r":uinput.KEY_R,"s":uinput.KEY_S,"t":uinput.KEY_T,
        "u":uinput.KEY_U,"v":uinput.KEY_V,"w":uinput.KEY_W,"x":uinput.KEY_X,
        "y":uinput.KEY_Y,"z":uinput.KEY_Z,
        "0":uinput.KEY_0,"1":uinput.KEY_1,"2":uinput.KEY_2,"3":uinput.KEY_3,
        "4":uinput.KEY_4,"5":uinput.KEY_5,"6":uinput.KEY_6,"7":uinput.KEY_7,
        "8":uinput.KEY_8,"9":uinput.KEY_9,
        " ":uinput.KEY_SPACE,"enter":uinput.KEY_ENTER,"backspace":uinput.KEY_BACKSPACE,
        "tab":uinput.KEY_TAB,"esc":uinput.KEY_ESC,"shift":uinput.KEY_LEFTSHIFT,
        "ctrl":uinput.KEY_LEFTCTRL,"alt":uinput.KEY_LEFTALT,
        "up":uinput.KEY_UP,"down":uinput.KEY_DOWN,"left":uinput.KEY_LEFT,"right":uinput.KEY_RIGHT,
        "home":uinput.KEY_HOME,"end":uinput.KEY_END,"delete":uinput.KEY_DELETE,
        "prior":uinput.KEY_PAGEUP,"next":uinput.KEY_PAGEDOWN,
        "f1":uinput.KEY_F1,"f2":uinput.KEY_F2,"f3":uinput.KEY_F3,
        "f4":uinput.KEY_F4,"f5":uinput.KEY_F5,"f6":uinput.KEY_F6,
        "-":uinput.KEY_MINUS,"=":uinput.KEY_EQUAL,
        "[":uinput.KEY_LEFTBRACE,"]":uinput.KEY_RIGHTBRACE,
        ";":uinput.KEY_SEMICOLON,"'":uinput.KEY_APOSTROPHE,
        ",":uinput.KEY_COMMA,".":uinput.KEY_DOT,
        "/":uinput.KEY_SLASH,"\\": uinput.KEY_BACKSLASH,"`":uinput.KEY_GRAVE,
    }
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
        '!':(uinput.KEY_1,True), '@':(uinput.KEY_2,True), '#':(uinput.KEY_3,True),
        '$':(uinput.KEY_4,True), '%':(uinput.KEY_5,True), '^':(uinput.KEY_6,True),
        '&':(uinput.KEY_7,True), '*':(uinput.KEY_8,True), '(':(uinput.KEY_9,True),
        ')':(uinput.KEY_0,True),
        ' ':(uinput.KEY_SPACE,False),'\n':(uinput.KEY_ENTER,False),
        '\t':(uinput.KEY_TAB,False),
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
    _dev = uinput.Device(_ALL)
    HAS_UINPUT = True
except Exception:
    HAS_UINPUT = False
    _dev = KEY_MAP = CHAR_MAP = None

# ── PIL ───────────────────────────────────────────────────────────────────────
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── Flask ─────────────────────────────────────────────────────────────────────
app  = Flask(__name__, static_folder=STATIC)
sock = Sock(app)

# ── Boot screen phone detection ───────────────────────────────────────────────
_phone_connected = False

@app.before_request
def _track_phone():
    global _phone_connected
    if not _phone_connected:
        ip = request.remote_addr or ""
        if ip and ip not in ("127.0.0.1", "::1"):
            _phone_connected = True

# ── Mode management ───────────────────────────────────────────────────────────
def get_mode():
    for f in [TMP_MODE, MODE_FILE]:
        try:
            m = open(f).read().strip()
            if m in MODES: return m
        except Exception:
            pass
    return "claude-dev"

def set_mode(mode, persist=False):
    try:
        with open(TMP_MODE, "w") as f: f.write(mode)
    except Exception: pass
    if persist:
        try:
            with open(MODE_FILE, "w") as f: f.write(mode)
        except Exception: pass

def get_boot_default():
    try:
        m = open(MODE_FILE).read().strip()
        return m if m in MODES else "claude-dev"
    except Exception:
        return "claude-dev"

def _find_xauth():
    for pat in ["/tmp/serverauth.*", "/tmp/.serverauth.*", "/home/peepo/.Xauthority"]:
        fs = glob.glob(pat)
        if fs: return fs[0]
    return None

def _xdo(*args):
    env = {"DISPLAY": ":0"}
    xa  = _find_xauth()
    if xa: env["XAUTHORITY"] = xa
    try:
        subprocess.Popen(["xdotool"] + list(args), env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print(f"[mock] xdotool {args}")

def _do_switch(mode):
    """Apply side effects of switching to a mode."""
    if mode == "gaming":
        subprocess.run(["pkill", "-f", "claude"], capture_output=True)
        peg = shutil.which("pegasus-fe")
        if peg:
            xa = _find_xauth() or "/home/peepo/.Xauthority"
            subprocess.Popen(
                ["runuser", "-u", "peepo", "--", "bash", "-c",
                 f"DISPLAY=:0 XAUTHORITY={xa} {peg}"],
                start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
    elif mode == "claude-dev":
        subprocess.run(["pkill", "pegasus-fe"], capture_output=True)
        _ensure_claude()
    elif mode == "headless":
        subprocess.run(["pkill", "pegasus-fe"], capture_output=True)
    # desktop: no action needed, X11 already running

def _ensure_claude():
    try:
        r = subprocess.run(
            ["runuser", "-u", "peepo", "--", "tmux", "-S", TMUX_SOCK,
             "has-session", "-t", TMUX_SESSION],
            capture_output=True
        )
        if r.returncode != 0:
            subprocess.run(["runuser", "-u", "peepo", "--", "tmux", "-S", TMUX_SOCK,
                            "new-session", "-d", "-s", TMUX_SESSION, "-x", "60", "-y", "30"])
            subprocess.run(["runuser", "-u", "peepo", "--", "tmux", "-S", TMUX_SOCK,
                            "new-window", "-t", TMUX_SESSION, "-n", TMUX_WINDOW])
            subprocess.run(["runuser", "-u", "peepo", "--", "tmux", "-S", TMUX_SOCK,
                            "send-keys", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}", "claude", "Enter"])
        threading.Thread(target=_watch_trust, daemon=True).start()
    except Exception as e:
        print(f"[claude] ensure failed: {e}")

# ── System info ───────────────────────────────────────────────────────────────
def _sys_info():
    out = {}
    # IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); out["ip"] = s.getsockname()[0]; s.close()
    except Exception: out["ip"] = "?"
    # CPU temp
    try:
        r = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True, timeout=2)
        out["temp"] = float(re.search(r"[\d.]+", r.stdout).group())
    except Exception: out["temp"] = None
    # Throttle
    try:
        r  = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2)
        th = int(r.stdout.strip().split("=")[-1], 16)
        out["throttle_now"]  = bool(th & 0x000F)
        out["throttle_ever"] = bool(th & 0xF000)
    except Exception:
        out["throttle_now"] = out["throttle_ever"] = False
    # RAM
    try:
        with open("/proc/meminfo") as f:
            mem = {l.split(":")[0]: int(l.split()[1]) for l in f if ":" in l}
        total = mem.get("MemTotal", 0)
        avail = mem.get("MemAvailable", 0)
        out["ram_used_mb"]  = (total - avail) // 1024
        out["ram_total_mb"] = total // 1024
        out["ram_pct"]      = int((total - avail) / total * 100) if total else 0
    except Exception:
        out["ram_used_mb"] = out["ram_total_mb"] = out["ram_pct"] = 0
    # Disk
    try:
        d = shutil.disk_usage("/")
        out["disk_pct"] = int(d.used / d.total * 100)
    except Exception: out["disk_pct"] = 0
    # Uptime
    try:
        secs  = int(float(open("/proc/uptime").read().split()[0]))
        h, r  = divmod(secs, 3600); m = r // 60
        out["uptime"] = f"{h}h{m:02d}m"
    except Exception: out["uptime"] = "?"
    return out

# ── tmux helpers ──────────────────────────────────────────────────────────────
def tmux(*args):
    return subprocess.run(
        ["runuser", "-u", "peepo", "--", "tmux", "-S", TMUX_SOCK] + list(args),
        capture_output=True, text=True
    )

def read_tmux():
    try:
        r   = tmux("capture-pane", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}", "-p", "-S", "-300")
        raw = ANSI_RE.sub("", r.stdout)
        return "\n".join(
            JUNK_RE.sub("", l).strip()
            for l in raw.splitlines() if len(JUNK_RE.sub("", l).strip()) > 1
        )
    except Exception: return ""

def _delta(prev: list, curr: list):
    """Return (new_lines, reset). Compares prev/curr to find only new content."""
    if not prev:
        return curr, True
    # Find longest suffix of prev that appears in curr (max 30 lines to check)
    max_overlap = min(len(prev), len(curr), 30)
    for overlap in range(max_overlap, 0, -1):
        tail = prev[-overlap:]
        for i in range(len(curr) - overlap, -1, -1):
            if curr[i:i + overlap] == tail:
                return curr[i + overlap:], False
    return curr, True  # no overlap → terminal cleared/reset

def parse_state(raw):
    lines  = [l for l in raw.splitlines() if l.strip()]
    tail   = lines[-30:] if len(lines) > 30 else lines
    screen = tail[-20:]
    state  = {"mode": "idle", "preview": tail[-80:], "options": [], "yesno": False}
    joined = "\n".join(screen)
    bottom = "\n".join(screen[-10:])
    thinking = bool(
        re.search(r"esc to interrupt|ctrl.c to interrupt", bottom, re.I) or
        re.search(r"[✻✢✦·⏺]\s+.*\d+\.?\d*s", bottom) or
        re.search(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏][\s\xa0]", bottom) or
        re.search(r"\d+\.\d+s\s*$", bottom) or
        re.search(r"Running|Executing|Writing|Reading|Searching|Compiling", bottom) and
        re.search(r"\d+s", bottom)
    )
    if thinking:
        state["mode"] = "thinking"
    opts = []; seen = set()
    for line in screen:
        # Match: "1. text", "> 1. text", "  2) text", etc.
        m = re.match(r"^[\s❯>\-]*(\d{1,2})[.)]\s+(.{2,})", line)
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            opts.append({"num": m.group(1), "label": m.group(2).strip()[:40]})
    has_cursor = any("❯" in l or bool(re.match(r"^\s*>\s*\d", l)) for l in screen)
    opts.sort(key=lambda o: int(o["num"]) if o["num"].isdigit() else 99)
    if opts and (len(opts) >= 2 or has_cursor) and not thinking:
        state["mode"] = "options"; state["options"] = opts[:6]
    if re.search(r"\[y[/ ]?n\]|\[yes[/ ]?no\]|\(y[/ ]?n\)", joined, re.I) and not thinking:
        state["mode"] = "yesno"; state["yesno"] = True
    return state

def _watch_trust():
    target = f"{TMUX_SESSION}:{TMUX_WINDOW}"
    for _ in range(40):
        time.sleep(1)
        raw = read_tmux()
        if re.search(r"trust this folder|Enter to confirm", raw, re.I):
            tmux("send-keys", "-t", target, "", "Enter"); return
        if "❯" in raw and "Try " in raw: return

threading.Thread(target=_watch_trust, daemon=True).start()

# ── Screen capture ────────────────────────────────────────────────────────────
SCREEN_W = 960; SCREEN_H = 540; SCREEN_FPS = 2; SCREEN_Q = 60
PI_W = 1920;    PI_H = 1080
_screen_lock    = threading.Lock()
_screen_frame   = b""
_screen_enabled = False

def _capture_loop():
    global _screen_frame, PI_W, PI_H
    interval = 1.0 / SCREEN_FPS
    while _screen_enabled:
        xa = _find_xauth()
        env = {"DISPLAY": ":0", "XAUTHORITY": xa or ""}
        try:
            r = subprocess.run(["xdpyinfo", "-display", ":0"], capture_output=True,
                               text=True, env=env, timeout=2)
            m = re.search(r"dimensions:\s+(\d+)x(\d+)", r.stdout)
            if m: PI_W, PI_H = int(m.group(1)), int(m.group(2))
        except Exception: pass
        try:
            r = subprocess.run(["scrot", "--quality", "70", "-"], capture_output=True,
                               env=env, timeout=5)
            if r.returncode == 0 and HAS_PIL:
                img = Image.open(io.BytesIO(r.stdout)).convert("RGB")
                img.thumbnail((SCREEN_W, SCREEN_H), Image.LANCZOS)
                buf = io.BytesIO(); img.save(buf, "JPEG", quality=SCREEN_Q)
                with _screen_lock: _screen_frame = buf.getvalue()
        except Exception: pass
        time.sleep(interval)
    with _screen_lock: _screen_frame = b""

# ── Audio ─────────────────────────────────────────────────────────────────────
_PW_ENV = {"HOME": "/home/peepo", "XDG_RUNTIME_DIR": "/run/user/1000",
           "PIPEWIRE_RUNTIME_DIR": "/run/user/1000"}
_DEFAULT_SINK = "alsa_output.platform-3f00b840.mailbox.stereo-fallback"

# ── Flask routes ──────────────────────────────────────────────────────────────

# ·· Boot screen ··
@app.route("/boot")
def boot_page():
    global _phone_connected
    _phone_connected = False  # reset on each boot visit
    return send_from_directory(STATIC, "boot.html")

@app.route("/api/qr.png")
def api_qr():
    try:
        import qrcode as _qr, io as _io
        info = _sys_info()
        url  = f"http://{info.get('ip','?')}:5000"
        q = _qr.QRCode(version=None,
                        error_correction=_qr.constants.ERROR_CORRECT_M,
                        box_size=7, border=2)
        q.add_data(url); q.make(fit=True)
        img = q.make_image(fill_color="#c8dce8", back_color="#060c14")
        buf = _io.BytesIO(); img.save(buf, "PNG"); buf.seek(0)
        return Response(buf.getvalue(), mimetype="image/png",
                        headers={"Cache-Control": "no-cache"})
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/api/boot/status")
def api_boot_status():
    info = _sys_info()
    return jsonify(
        connected=_phone_connected,
        ip=info.get("ip", "?"),
        temp=info.get("temp"),
        uptime=info.get("uptime", ""),
        mode=get_mode(),
    )

# ·· Cockpit core ··
@app.route("/")
def cockpit_home():
    return send_from_directory(STATIC, "index.html")

@app.route("/claude")
def claude_ui():
    return send_from_directory(PHONE_STATIC, "index.html")

@app.route("/gaming")
def gaming_ui():
    return send_from_directory(PAD_STATIC, "index.html")

@app.route("/api/sys/info")
def api_sys_info():
    return jsonify(**_sys_info())

@app.route("/api/mode/status")
def api_mode_status():
    mode = get_mode()
    return jsonify(mode=mode, default=get_boot_default(), modes={
        k: {"label": v["label"], "color": v["color"], "ui": v["ui"]}
        for k, v in MODES.items()
    })

@app.route("/api/mode/switch", methods=["POST"])
def api_mode_switch():
    d    = request.get_json(force=True) or {}
    mode = d.get("mode", "")
    if mode not in MODES:
        return jsonify(error="unknown mode"), 400
    _do_switch(mode)
    set_mode(mode)
    return jsonify(ok=True, mode=mode, ui=MODES[mode]["ui"])

@app.route("/api/mode/default", methods=["POST"])
def api_mode_default():
    d    = request.get_json(force=True) or {}
    mode = d.get("mode", get_mode())
    if mode not in MODES:
        return jsonify(error="unknown mode"), 400
    set_mode(mode, persist=True)
    return jsonify(ok=True, default=mode)

@app.route("/power/reboot", methods=["POST"])
def power_reboot():
    threading.Timer(1.0, lambda: subprocess.run(["reboot"])).start()
    return jsonify(ok=True)

@app.route("/power/shutdown", methods=["POST"])
def power_shutdown():
    threading.Timer(1.0, lambda: subprocess.run(["poweroff"])).start()
    return jsonify(ok=True)

@app.route("/ping")
def ping():
    return jsonify(ok=True)

# ·· Claude / phone-input routes ··
@app.route("/claude-state")
def claude_state():
    def gen():
        sent_lines = []
        last_sig = None  # (mode, options_str) for change detection
        while True:
            state = parse_state(read_tmux())
            new_lines, reset = _delta(sent_lines, state["preview"])
            sent_lines = state["preview"]
            sig = (state["mode"], str(state["options"]))
            changed = sig != last_sig or new_lines or reset
            if changed:
                last_sig = sig
                out = {
                    "mode":      state["mode"],
                    "options":   state["options"],
                    "new_lines": new_lines,
                    "reset":     reset,
                }
                yield f"data: {json.dumps(out)}\n\n"
            else:
                yield ": ping\n\n"
            time.sleep(0.6)
    return Response(stream_with_context(gen()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/prompt", methods=["POST"])
def prompt():
    d   = request.get_json(force=True) or {}
    txt = d.get("text", "").strip()
    if not txt: return jsonify(ok=False)
    target = f"{TMUX_SESSION}:{TMUX_WINDOW}"
    tmux("send-keys", "-t", target, "-l", txt)
    tmux("send-keys", "-t", target, "Enter")
    return jsonify(ok=True, chars=len(txt))

@app.route("/choose", methods=["POST"])
def choose():
    d      = request.get_json(force=True) or {}
    choice = d.get("choice", "")
    self_complete = {"esc", "ctrl-c", "ctrl-z", "enter"}
    special = {"esc": "Escape", "ctrl-c": "C-c", "ctrl-z": "C-z", "enter": "Enter"}
    key  = special.get(choice.lower(), choice)
    args = ["send-keys", "-t", f"{TMUX_SESSION}:{TMUX_WINDOW}", key]
    if choice.lower() not in self_complete: args.append("Enter")
    tmux(*args)
    return jsonify(ok=True)

@app.route("/key", methods=["POST"])
def key():
    if not HAS_UINPUT: return jsonify(ok=False, reason="no uinput")
    d      = request.get_json(force=True) or {}
    k      = d.get("key", "").lower()
    action = d.get("action", "tap")
    code   = KEY_MAP.get(k)
    if not code: return jsonify(ok=False)
    if action == "tap":
        _dev.emit(code, 1); _dev.emit(code, 0); _dev.syn()
    elif action == "down":
        _dev.emit(code, 1); _dev.syn()
    elif action == "up":
        _dev.emit(code, 0); _dev.syn()
    return jsonify(ok=True)

@app.route("/text", methods=["POST"])
def text():
    if not HAS_UINPUT: return jsonify(ok=False, reason="no uinput")
    txt = (request.get_json(force=True) or {}).get("text", "")
    for ch in txt:
        entry = CHAR_MAP.get(ch)
        if not entry: continue
        code, shift = entry
        if shift:
            _dev.emit(uinput.KEY_LEFTSHIFT, 1); _dev.syn()
            _dev.emit(code, 1); _dev.emit(code, 0); _dev.syn()
            _dev.emit(uinput.KEY_LEFTSHIFT, 0); _dev.syn()
        else:
            _dev.emit(code, 1); _dev.emit(code, 0); _dev.syn()
    return jsonify(ok=True)

@app.route("/mouse", methods=["POST"])
def mouse_post():
    if not HAS_UINPUT: return jsonify(ok=False)
    d = request.get_json(force=True) or {}
    if "dx" in d or "dy" in d:
        dx, dy = int(d.get("dx", 0)), int(d.get("dy", 0))
        if dx: _dev.emit(uinput.REL_X, dx)
        if dy: _dev.emit(uinput.REL_Y, dy)
        _dev.syn()
    elif d.get("btn") in ("click", "leftclick"):
        _dev.emit(uinput.BTN_LEFT, 1); _dev.emit(uinput.BTN_LEFT, 0); _dev.syn()
    elif d.get("btn") == "rightclick":
        _dev.emit(uinput.BTN_RIGHT, 1); _dev.emit(uinput.BTN_RIGHT, 0); _dev.syn()
    elif "scroll" in d:
        _dev.emit(uinput.REL_WHEEL, int(d["scroll"])); _dev.syn()
    return jsonify(ok=True)

@app.route("/screen-toggle", methods=["POST"])
def screen_toggle():
    global _screen_enabled
    _screen_enabled = not _screen_enabled
    if _screen_enabled:
        threading.Thread(target=_capture_loop, daemon=True).start()
    return jsonify(ok=True, enabled=_screen_enabled)

@app.route("/screen-info")
def screen_info():
    return jsonify(w=PI_W, h=PI_H)

@app.route("/screen-stream")
def screen_stream():
    if not _screen_enabled: return Response("disabled", status=503)
    def gen():
        try:
            last = None
            while _screen_enabled:
                with _screen_lock: frame = _screen_frame
                if frame and frame is not last:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                    last = frame
                time.sleep(0.08)
        except GeneratorExit: pass
    return Response(stream_with_context(gen()),
                    mimetype="multipart/x-mixed-replace; boundary=frame",
                    headers={"Cache-Control": "no-cache"})

@app.route("/screen-input", methods=["POST"])
def screen_input():
    d    = request.get_json(force=True) or {}
    kind = d.get("type", ""); x = d.get("x", 0); y = d.get("y", 0)
    scroll = d.get("scroll", 0)
    xa   = _find_xauth()
    xenv = {"DISPLAY": ":0", "XAUTHORITY": xa or ""}
    if kind == "click":
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], env=xenv)
    elif kind == "rightclick":
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "3"], env=xenv)
    elif kind == "move":
        subprocess.run(["xdotool", "mousemove", str(x), str(y)], env=xenv)
    elif kind == "down":
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "mousedown", "1"], env=xenv)
    elif kind == "up":
        subprocess.run(["xdotool", "mousemove", str(x), str(y), "mouseup", "1"], env=xenv)
    elif kind == "scroll":
        btn = "4" if scroll > 0 else "5"
        for _ in range(abs(scroll)): subprocess.run(["xdotool", "click", btn], env=xenv)
    return jsonify(ok=True)

@app.route("/audio-stream")
def audio_stream():
    def gen():
        pw_cmd = ("XDG_RUNTIME_DIR=/run/user/1000 PIPEWIRE_RUNTIME_DIR=/run/user/1000 "
                  f"pw-record --target '{_DEFAULT_SINK}' --rate 44100 --channels 2 -")
        pw = subprocess.Popen(["runuser", "-u", "peepo", "--", "bash", "-c", pw_cmd],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
        ff = subprocess.Popen(
            ["ffmpeg", "-loglevel", "quiet", "-f", "s16le", "-ar", "44100", "-ac", "2",
             "-i", "pipe:0", "-acodec", "libmp3lame", "-ab", "96k", "-ar", "44100",
             "-f", "mp3", "pipe:1"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        def _pump():
            try:
                rem = 24
                while rem > 0:
                    d = pw.stdout.read(rem);
                    if not d: break
                    rem -= len(d)
                while True:
                    d = pw.stdout.read(4096)
                    if not d: break
                    ff.stdin.write(d); ff.stdin.flush()
            except Exception: pass
            finally:
                try: ff.stdin.close()
                except Exception: pass
        threading.Thread(target=_pump, daemon=True).start()
        try:
            while True:
                chunk = ff.stdout.read1(8192)
                if not chunk: break
                yield chunk
        finally:
            ff.kill(); pw.kill(); ff.wait(); pw.wait()
    return Response(stream_with_context(gen()), mimetype="audio/mpeg",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/audio-volume", methods=["POST"])
def audio_volume():
    vol = max(0, min(100, int((request.get_json(force=True) or {}).get("vol", 80))))
    subprocess.run(["runuser", "-u", "peepo", "--", "wpctl", "set-volume",
                    "@DEFAULT_AUDIO_SINK@", f"{vol}%"], env=_PW_ENV, timeout=3)
    return jsonify(ok=True, vol=vol)

@app.route("/claude-restart", methods=["POST"])
def claude_restart():
    target = f"{TMUX_SESSION}:{TMUX_WINDOW}"
    tmux("send-keys", "-t", target, "C-c"); time.sleep(0.4)
    tmux("send-keys", "-t", target, "q", "Enter"); time.sleep(0.4)
    tmux("send-keys", "-t", target, "claude", "Enter")
    threading.Thread(target=_watch_trust, daemon=True).start()
    return jsonify(ok=True)

# ·· Gamepad (pegasus-pad) ··
PEGASUS_KEYS = {
    "up":"Up","down":"Down","left":"Left","right":"Right",
    "a":"Return","b":"Escape","x":"F1","y":"F2",
    "l1":"Prior","r1":"Next","l2":"F6","r2":"F5",
    "select":"BackSpace","start":"Return","home":"Escape",
}
GAME_KEYS = {
    "up":"Up","down":"Down","left":"Left","right":"Right",
    "a":"x","b":"z","x":"s","y":"a",
    "l1":"q","r1":"w","l2":"e","r2":"r",
    "select":"shift","start":"Return","home":"Escape",
}

@app.route("/btn", methods=["POST"])
def btn():
    d      = request.get_json(force=True) or {}
    name   = d.get("btn", "")
    action = d.get("action", "press")
    mode_g = d.get("mode", "pegasus")
    km     = PEGASUS_KEYS if mode_g == "pegasus" else GAME_KEYS
    key    = km.get(name)
    if key: _xdo({"press": "key", "down": "keydown", "up": "keyup"}.get(action, "key"),
                  "--clearmodifiers", key)
    return jsonify(ok=True)

# ·· Git + file ··
def _git(*args):
    return subprocess.run(["git", "-C", GIT_DIR] + list(args),
                          capture_output=True, text=True, timeout=10).stdout.strip()

@app.route("/git/log")
def git_log():
    raw     = _git("log", "--format=%H|%h|%ar|%s", "-30")
    commits = []
    for line in raw.splitlines():
        p = line.split("|", 3)
        if len(p) == 4: commits.append({"hash":p[0],"short":p[1],"age":p[2],"msg":p[3]})
    return jsonify(commits=commits,
                   branch=_git("rev-parse","--abbrev-ref","HEAD"),
                   status=_git("status","--short"))

@app.route("/git/show/<commit_hash>")
def git_show(commit_hash):
    if not re.match(r'^[0-9a-f]{4,40}$', commit_hash):
        return jsonify(error="invalid hash"), 400
    return jsonify(detail=_git("show","--stat",
                               "--format=Author: %an%nDate: %ar%n%n%s%n%n%b",
                               commit_hash)[:6000])

@app.route("/git/pull", methods=["POST"])
def git_pull():
    r = subprocess.run(["git","-C",GIT_DIR,"pull"],capture_output=True,text=True,timeout=30)
    return jsonify(ok=True, out=(r.stdout+r.stderr)[:500])

@app.route("/file")
def file_read():
    path = request.args.get("path","")
    full = os.path.normpath(os.path.join(GIT_DIR, path.lstrip("/")))
    if not full.startswith(GIT_DIR): return jsonify(error="forbidden"), 403
    try:
        with open(full, encoding="utf-8") as f: return jsonify(content=f.read())
    except Exception as e: return jsonify(error=str(e)), 404

@app.route("/file", methods=["POST"])
def file_write():
    d    = request.get_json(force=True) or {}
    path = d.get("path",""); content = d.get("content","")
    full = os.path.normpath(os.path.join(GIT_DIR, path.lstrip("/")))
    if not full.startswith(GIT_DIR): return jsonify(error="forbidden"), 403
    try:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f: f.write(content)
        return jsonify(ok=True)
    except Exception as e: return jsonify(error=str(e)), 500

# ·· WebSocket (mouse) ··
@sock.route("/ws")
def ws(ws):
    while True:
        try:
            d = json.loads(ws.receive())
            mouse_post.__wrapped__ = True
            if "dx" in d or "dy" in d:
                if HAS_UINPUT:
                    dx, dy = int(d.get("dx",0)), int(d.get("dy",0))
                    if dx: _dev.emit(uinput.REL_X, dx)
                    if dy: _dev.emit(uinput.REL_Y, dy)
                    _dev.syn()
            elif d.get("btn") in ("click","leftclick"):
                if HAS_UINPUT:
                    _dev.emit(uinput.BTN_LEFT,1); _dev.emit(uinput.BTN_LEFT,0); _dev.syn()
            elif d.get("btn") == "rightclick":
                if HAS_UINPUT:
                    _dev.emit(uinput.BTN_RIGHT,1); _dev.emit(uinput.BTN_RIGHT,0); _dev.syn()
            elif "scroll" in d:
                if HAS_UINPUT:
                    _dev.emit(uinput.REL_WHEEL, int(d["scroll"])); _dev.syn()
        except Exception: break

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
    except Exception: ip = "localhost"
    print(f"\n  Pi Cockpit  →  http://{ip}:5000\n")
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)
