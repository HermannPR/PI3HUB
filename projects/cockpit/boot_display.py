#!/usr/bin/env python3
"""
JarvisPi3 boot display — ultra-lightweight Tkinter kiosk.
~15MB RAM, exits when phone connects (frees memory for Claude Code).
"""
import os, time, json, threading
import urllib.request
import tkinter as tk
from tkinter import font as tkfont

try:
    import qrcode as _qrc
    _QR_MOD = True
except ImportError:
    _QR_MOD = False

URL_STATUS = "http://localhost:5000/api/boot/status"
URL_TAMAGO = "http://localhost:5000/api/tamago"

BG      = "#02050a"
BG2     = "#060c14"
ACCENT  = "#2a7a96"
BRIGHT  = "#b8d0dc"
TEXT    = "#2a4858"
DIM     = "#101c28"
QR_FILL = "#c8dce8"


def main():
    os.environ.setdefault("DISPLAY", ":0")

    root = tk.Tk()
    root.title("JarvisPi3")
    root.configure(bg=BG)
    root.attributes("-fullscreen", True)
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    W = root.winfo_screenwidth()
    H = root.winfo_screenheight()

    cv = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
    cv.pack(fill="both", expand=True)

    # Fonts
    size_logo = max(36, H // 13)
    size_sub  = max(10, H // 72)
    size_ip   = max(12, H // 56)
    size_foot = max(9,  H // 82)

    fn_logo = tkfont.Font(family="Courier New", size=size_logo, weight="bold")
    fn_sub  = tkfont.Font(family="Courier New", size=size_sub)
    fn_ip   = tkfont.Font(family="Courier New", size=size_ip)
    fn_foot = tkfont.Font(family="Courier New", size=size_foot)

    QR   = min(H // 3, W // 5, 200)
    cx   = W // 2
    qr_y0 = H // 2 - QR // 2
    qr_y1 = qr_y0 + QR

    # Static elements
    logo_y = qr_y0 - fn_sub.metrics("linespace") - 10
    sub_y  = qr_y0 - 6
    cv.create_text(cx, logo_y, text="J A R V I S  P I 3",
                   fill=BRIGHT, font=fn_logo, anchor="s")
    cv.create_text(cx, sub_y, text="RASPBERRY PI CONTROL INTERFACE",
                   fill=DIM, font=fn_sub, anchor="s")

    # Corner brackets
    BC = "#142030"
    BL = 22
    for bx, by, flip_x, flip_y in [
        (18,   18,   False, False),
        (W-18, 18,   True,  False),
        (18,   H-50, False, True),
        (W-18, H-50, True,  True),
    ]:
        x0 = bx - BL if flip_x else bx
        y0 = by - BL if flip_y else by
        x1 = x0 + BL; y1 = y0 + BL
        top_y = y1 if flip_y else y0
        lft_x = x1 if flip_x else x0
        cv.create_line(x0, top_y, x1, top_y, fill=BC)
        cv.create_line(lft_x, y0, lft_x, y1, fill=BC)

    # Footer separator
    cv.create_line(20, H-44, W-20, H-44, fill="#0a1820")

    # QR placeholder box
    cv.create_rectangle(cx-QR//2-1, qr_y0-1, cx+QR//2+1, qr_y1+1,
                        outline=DIM, fill=BG2)

    # Dynamic items
    border_id = cv.create_rectangle(cx-QR//2-5, qr_y0-5,
                                    cx+QR//2+5, qr_y1+5,
                                    outline=DIM, fill="")
    ip_id     = cv.create_text(cx, qr_y1+18, text="--",
                               fill=ACCENT, font=fn_ip, anchor="n")
    status_id = cv.create_text(cx, qr_y1+46, text="AWAITING CONNECTION_",
                               fill=TEXT, font=fn_sub, anchor="n")
    temp_id   = cv.create_text(cx-130, H-26, text="TEMP --",
                               fill=DIM, font=fn_foot, anchor="center")
    up_id     = cv.create_text(cx,     H-26, text="UP --",
                               fill=DIM, font=fn_foot, anchor="center")
    mode_id   = cv.create_text(cx+130, H-26, text="MODE --",
                               fill=DIM, font=fn_foot, anchor="center")

    # Tamagotchi widget (below status)
    row_gap   = max(16, H // 65)
    tama_y0   = qr_y1 + 82
    tama_id   = cv.create_text(cx, tama_y0, text="TAMA  ●  --",
                               fill=DIM, font=fn_foot, anchor="n")
    tama_rows = [
        cv.create_text(cx, tama_y0 + row_gap * (i + 1) + 4, text="",
                       fill=DIM, font=fn_foot, anchor="n")
        for i in range(5)
    ]

    # State
    state = {
        "snap":      {},
        "qr_matrix": None,
        "qr_drawn":  False,
        "tamago":    None,
        "connected": False,
        "exiting":   False,
        "cur_on":    True,
    }

    def fetch_loop():
        while not state["exiting"]:
            # System status
            try:
                with urllib.request.urlopen(URL_STATUS, timeout=3) as r:
                    state["snap"] = json.loads(r.read())
            except Exception:
                pass

            # QR matrix — generate once when we have the IP
            if state["qr_matrix"] is None and _QR_MOD:
                ip = state["snap"].get("ip", "")
                if ip and ip != "?":
                    try:
                        q = _qrc.QRCode(version=None,
                                        error_correction=_qrc.constants.ERROR_CORRECT_M,
                                        box_size=1, border=2)
                        q.add_data(f"http://{ip}:5000")
                        q.make(fit=True)
                        state["qr_matrix"] = q.get_matrix()
                    except Exception:
                        pass

            # Tamagotchi leaderboard
            try:
                with urllib.request.urlopen(URL_TAMAGO, timeout=4) as r:
                    state["tamago"] = json.loads(r.read())
            except Exception:
                if state["tamago"] is None:
                    state["tamago"] = {"online": False, "scores": []}

            time.sleep(2)

    threading.Thread(target=fetch_loop, daemon=True).start()

    pulse_t = [0.0]

    def tick():
        if state["exiting"]:
            root.destroy()
            return

        d = state["snap"]

        if d.get("connected") and not state["connected"]:
            state["connected"] = True
            cv.itemconfig(status_id, text="CONNECTION ESTABLISHED", fill=ACCENT)
            root.after(1600, root.destroy)
            return

        # IP
        cv.itemconfig(ip_id, text=f"http://{d.get('ip','--')}:5000")

        # Footer stats
        temp = d.get("temp")
        cv.itemconfig(temp_id, text=f"TEMP  {temp:.1f}C" if temp else "TEMP  --")
        cv.itemconfig(up_id,   text=f"UP  {d.get('uptime','--')}")
        cv.itemconfig(mode_id, text=f"MODE  {d.get('mode','--').replace('-',' ').upper()}")

        # Cursor blink
        state["cur_on"] = not state["cur_on"]
        cv.itemconfig(status_id,
                      text="AWAITING CONNECTION" + ("_" if state["cur_on"] else " "))

        # Pulsing border
        pulse_t[0] = (pulse_t[0] + 0.06) % 1.0
        lum = 0.10 + 0.22 * abs(pulse_t[0] * 2 - 1)
        r2 = min(255, int(42 * lum * 3.5))
        g2 = min(255, int(122 * lum * 2))
        b2 = min(255, int(150 * lum * 2))
        cv.itemconfig(border_id, outline=f"#{r2:02x}{g2:02x}{b2:02x}")

        # QR — draw as canvas rectangles once the matrix is ready
        if state["qr_matrix"] and not state["qr_drawn"]:
            matrix = state["qr_matrix"]
            n      = len(matrix)
            cell   = QR / n
            x0     = cx - QR // 2
            y0     = H // 2 - QR // 2
            for row in range(n):
                for col in range(n):
                    if matrix[row][col]:
                        cv.create_rectangle(
                            x0 + col * cell,       y0 + row * cell,
                            x0 + (col + 1) * cell, y0 + (row + 1) * cell,
                            fill=QR_FILL, outline=""
                        )
            state["qr_drawn"] = True

        # Tamagotchi widget
        tama = state.get("tamago")
        if tama is not None:
            if tama.get("online"):
                cv.itemconfig(tama_id, text="TAMA  ●  ONLINE", fill=ACCENT)
                scores = tama.get("scores", [])[:5]
                for i, rid in enumerate(tama_rows):
                    if i < len(scores):
                        s = scores[i]
                        cv.itemconfig(rid,
                                      text=f"#{s['rank']}  {s['nick']}  {s['score']:,}",
                                      fill=TEXT)
                    else:
                        cv.itemconfig(rid, text="")
            else:
                cv.itemconfig(tama_id, text="TAMA  ●  OFFLINE", fill=DIM)
                for rid in tama_rows:
                    cv.itemconfig(rid, text="")

        root.after(550, tick)

    root.bind("<Key>",    lambda e: root.destroy())
    root.bind("<Button>", lambda e: root.destroy())

    root.after(1000, tick)
    root.mainloop()


if __name__ == "__main__":
    main()
