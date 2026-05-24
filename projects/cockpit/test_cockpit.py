#!/usr/bin/env python3
"""
Cockpit health check — run as peepo (no sudo needed).
Usage: python3 test_cockpit.py
"""
import urllib.request, urllib.error, json, subprocess, os, sys, socket, time

BASE = "http://localhost:5000"
W    = 44  # line width for phone

PASS = "✓"; FAIL = "✗"

results = []

def check(group, name, ok, detail=""):
    results.append((group, name, ok, detail))

def get(path, timeout=3, max_bytes=8192):
    try:
        with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
            body = r.read(max_bytes)
            return r.status, body, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, b"", {}
    except Exception:
        return 0, b"", {}

def head(path, timeout=3):
    """Check reachability of a streaming endpoint without reading body."""
    try:
        req = urllib.request.Request(BASE + path, method="GET")
        r = urllib.request.urlopen(req, timeout=timeout)
        status = r.status
        ct = r.headers.get("Content-Type", "")
        r.close()
        return status, ct
    except Exception:
        return 0, ""

# ── API ───────────────────────────────────────────────────────────────────────
status, body, _ = get("/ping")
check("API", "server alive", status == 200)

status, body, _ = get("/api/sys/info")
if status == 200:
    d = json.loads(body)
    temp = d.get("temp")
    ram  = d.get("ram_pct", "?")
    check("API", "sys/info", True, f"temp={temp}C ram={ram}%")
else:
    check("API", "sys/info", False, f"HTTP {status}")

status, body, hdrs = get("/api/qr.png")
if status == 200:
    ct = hdrs.get("Content-Type", "")
    check("API", "QR image", "image/png" in ct, f"{len(body)}B")
else:
    check("API", "QR image", False, f"HTTP {status}")

status, body, _ = get("/api/mode/status")
if status == 200:
    d = json.loads(body)
    check("API", "mode status", "mode" in d, d.get("mode","?"))
else:
    check("API", "mode status", False, f"HTTP {status}")

status, body, _ = get("/api/tamago")
if status == 200:
    d = json.loads(body)
    online = d.get("online", False)
    scores = len(d.get("scores", []))
    check("API", "tamago proxy", True,
          f"ONLINE scores={scores}" if online else "OFFLINE (expected if no URL)")
else:
    check("API", "tamago proxy", False, f"HTTP {status}")

status, ct = head("/claude-state")
check("API", "SSE stream", status == 200 and "event-stream" in ct)

# ── SYSTEM ───────────────────────────────────────────────────────────────────
TMUX_SOCK = "/tmp/tmux-1000/default"

r = subprocess.run(
    ["tmux", "-S", TMUX_SOCK, "has-session", "-t", "setup"],
    capture_output=True)
check("SYS", "tmux session", r.returncode == 0)

r = subprocess.run(
    ["tmux", "-S", TMUX_SOCK, "list-windows", "-t", "setup"],
    capture_output=True, text=True)
check("SYS", "tmux claude window", "claude" in r.stdout)

r = subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True)
if r.returncode == 0:
    check("SYS", "vcgencmd", True, r.stdout.strip())
else:
    check("SYS", "vcgencmd", False)

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2); s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]; s.close()
    check("SYS", "IP detect", ip != "?", ip)
except Exception as e:
    check("SYS", "IP detect", False, str(e)[:30])

try:
    up = float(open("/proc/uptime").read().split()[0])
    h, r2 = divmod(int(up), 3600); m = r2 // 60
    check("SYS", "uptime", True, f"{h}h{m:02d}m")
except Exception:
    check("SYS", "uptime", False)

# ── IMPORTS ───────────────────────────────────────────────────────────────────
for mod, label in [
    ("flask",        "flask"),
    ("flask_sock",   "flask_sock"),
    ("qrcode",       "qrcode"),
    ("PIL",          "pillow"),
    ("uinput",       "uinput"),
]:
    try:
        __import__(mod)
        check("IMPORT", label, True)
    except ImportError:
        check("IMPORT", label, False, "not installed")

try:
    import qrcode as _qr
    q = _qr.QRCode(version=None, box_size=1, border=1)
    q.add_data("http://test"); q.make(fit=True)
    m = q.get_matrix()
    check("IMPORT", "qrcode matrix", isinstance(m, list), f"{len(m)}x{len(m)}")
except Exception as e:
    check("IMPORT", "qrcode matrix", False, str(e)[:30])

# ── TAMAGOTCHI ────────────────────────────────────────────────────────────────
# TAMAGO_URL is set inside the server process (start.sh), not the test shell.
# Read it via the /api/tamago endpoint instead.
tamago_url = os.environ.get("TAMAGO_URL", "")
if not tamago_url:
    # Try to infer from start.sh
    try:
        sh = open(os.path.join(os.path.dirname(__file__), "start.sh")).read()
        import re as _re
        m = _re.search(r'TAMAGO_URL:-([^}]+)\}', sh)
        if m: tamago_url = m.group(1).strip('"\'')
    except Exception:
        pass
placeholder = "your-tamagotchi.vercel.app" in tamago_url or tamago_url == ""
check("TAMA", "TAMAGO_URL set", not placeholder,
      tamago_url[:40] if tamago_url else "not set")

if tamago_url and not placeholder:
    try:
        req = urllib.request.Request(
            tamago_url.rstrip("/") + "/api/leaderboard",
            headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read())
            # mildred-pierce returns {users:[...]} or legacy [{nick,score}]
            entries = d.get("users", d) if isinstance(d, dict) else d
            check("TAMA", "vercel leaderboard", isinstance(entries, list),
                  f"{len(entries)} entries")
    except Exception as e:
        check("TAMA", "vercel leaderboard", False, str(e)[:35])

# ── PRINT ─────────────────────────────────────────────────────────────────────
print()
print("COCKPIT HEALTH CHECK")
print("─" * W)

cur_group = None
passed = failed = 0
for group, name, ok, detail in results:
    if group != cur_group:
        if cur_group is not None:
            print()
        print(f"  {group}")
        cur_group = group
    mark  = PASS if ok else FAIL
    line  = f"    {mark} {name}"
    if detail:
        pad = max(1, W - len(line) - len(detail))
        line = line + " " * pad + detail
    print(line[:W])
    if ok: passed += 1
    else:  failed += 1

print()
print("─" * W)
score = f"PASSED {passed}  FAILED {failed}"
total = passed + failed
bar   = "█" * passed + "░" * failed
print(f"  {score}")
print(f"  [{bar}] {passed}/{total}")
print()

sys.exit(0 if failed == 0 else 1)
