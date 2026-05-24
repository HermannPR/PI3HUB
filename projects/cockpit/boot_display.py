#!/usr/bin/env python3
"""
NEXUS boot display — ultra-lightweight Tkinter kiosk.
~15MB RAM, exits when phone connects (frees memory for Claude Code).
"""
import os, sys, time, json, threading, io
import urllib.request
import tkinter as tk
from tkinter import font as tkfont
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

URL_STATUS = "http://localhost:5000/api/boot/status"
URL_QR     = "http://localhost:5000/api/qr.png"

BG       = "#02050a"
BG2      = "#060c14"
ACCENT   = "#2a7a96"
BRIGHT   = "#b8d0dc"
TEXT     = "#2a4858"
DIM      = "#101c28"
FOOT_BG  = "#030710"


def main():
    os.environ.setdefault("DISPLAY", ":0")

    root = tk.Tk()
    root.title("NEXUS")
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

    QR = min(H // 3, W // 5, 200)
    cx = W // 2
    qr_y0 = H // 2 - QR // 2
    qr_y1 = qr_y0 + QR

    # Static elements
    logo_y  = qr_y0 - fn_sub.metrics("linespace") - 10
    sub_y   = qr_y0 - 6

    cv.create_text(cx, logo_y, text="N  E  X  U  S",
                   fill=BRIGHT, font=fn_logo, anchor="s")
    cv.create_text(cx, sub_y, text="RASPBERRY PI CONTROL INTERFACE",
                   fill=DIM, font=fn_sub, anchor="s")

    # Corner brackets
    BL  = 22
    BC  = "#142030"
    for bx, by, flip_x, flip_y in [
        (18,    18,    False, False),
        (W-18,  18,    True,  False),
        (18,    H-50,  False, True),
        (W-18,  H-50,  True,  True),
    ]:
        x0 = bx - BL if flip_x else bx
        y0 = by - BL if flip_y else by
        x1 = x0 + BL; y1 = y0 + BL
        top_y = y1 if flip_y else y0
        bot_y = y0 if flip_y else y1
        lft_x = x1 if flip_x else x0
        rgt_x = x0 if flip_x else x1
        cv.create_line(x0, top_y, x1, top_y, fill=BC)
        cv.create_line(lft_x, y0, lft_x, y1, fill=BC)

    # Footer separator
    cv.create_line(20, H-44, W-20, H-44, fill="#0a1820")

    # QR placeholder box
    cv.create_rectangle(cx-QR//2-1, qr_y0-1, cx+QR//2+1, qr_y1+1,
                        outline=DIM, fill=BG2)

    # Dynamic items (updated by poll)
    qr_item    = None
    border_id  = cv.create_rectangle(cx-QR//2-5, qr_y0-5,
                                     cx+QR//2+5, qr_y1+5,
                                     outline=DIM, fill="")
    ip_id      = cv.create_text(cx, qr_y1+18, text="--",
                                fill=ACCENT, font=fn_ip, anchor="n")
    status_id  = cv.create_text(cx, qr_y1+46, text="AWAITING CONNECTION_",
                                fill=TEXT, font=fn_sub, anchor="n")
    temp_id    = cv.create_text(cx-130, H-26, text="TEMP --",
                                fill=DIM, font=fn_foot, anchor="center")
    up_id      = cv.create_text(cx,     H-26, text="UP --",
                                fill=DIM, font=fn_foot, anchor="center")
    mode_id    = cv.create_text(cx+130, H-26, text="MODE --",
                                fill=DIM, font=fn_foot, anchor="center")

    # State
    state = {
        "snap":      {},
        "qr_img":    None,
        "connected": False,
        "exiting":   False,
        "cur_on":    True,
    }

    def fetch_loop():
        while not state["exiting"]:
            try:
                with urllib.request.urlopen(URL_STATUS, timeout=3) as r:
                    state["snap"] = json.loads(r.read())
            except Exception:
                pass
            if state["qr_img"] is None and HAS_PIL:
                try:
                    with urllib.request.urlopen(URL_QR, timeout=5) as r:
                        raw = r.read()
                    pil = Image.open(io.BytesIO(raw)).resize((QR, QR), Image.NEAREST)
                    state["qr_img"] = pil
                except Exception:
                    pass
            time.sleep(2)

    threading.Thread(target=fetch_loop, daemon=True).start()

    # Pulse border phase (0→1 cycle)
    pulse_t = [0.0]
    tk_qr_ref = [None]  # keep reference to avoid GC

    def tick():
        if state["exiting"]:
            root.destroy()
            return

        d = state["snap"]

        if d.get("connected") and not state["connected"]:
            state["connected"] = True
            cv.itemconfig(status_id, text="CONNECTION ESTABLISHED", fill=ACCENT)
            root.after(1600, lambda: setattr(state, "_ex", True) or root.destroy())
            return

        # IP
        ip = d.get("ip", "--")
        cv.itemconfig(ip_id, text=f"http://{ip}:5000")

        # Stats
        temp = d.get("temp")
        cv.itemconfig(temp_id, text=f"TEMP  {temp:.1f}C" if temp else "TEMP  --")
        cv.itemconfig(up_id,   text=f"UP  {d.get('uptime','--')}")
        cv.itemconfig(mode_id, text=f"MODE  {d.get('mode','--').replace('-',' ').upper()}")

        # Cursor blink
        state["cur_on"] = not state["cur_on"]
        suf = "_" if state["cur_on"] else " "
        cv.itemconfig(status_id, text="AWAITING CONNECTION" + suf)

        # Pulsing border
        pulse_t[0] = (pulse_t[0] + 0.06) % 1.0
        lum = 0.10 + 0.22 * abs(pulse_t[0] * 2 - 1)
        r2 = int(42 * lum * 3.5); g2 = int(122 * lum * 2); b2 = int(150 * lum * 2)
        r2 = min(255, r2); g2 = min(255, g2); b2 = min(255, b2)
        bc = f"#{r2:02x}{g2:02x}{b2:02x}"
        cv.itemconfig(border_id, outline=bc)

        # QR image (once loaded)
        if state["qr_img"] is not None and tk_qr_ref[0] is None:
            tk_img = ImageTk.PhotoImage(state["qr_img"])
            tk_qr_ref[0] = tk_img
            cv.delete("qr_ph")
            cv.create_image(cx, H//2, image=tk_img, anchor="center", tags="qr")

        root.after(550, tick)  # ~1.8fps for updates (very light)

    # Key/click to skip
    root.bind("<Key>",    lambda e: root.destroy())
    root.bind("<Button>", lambda e: root.destroy())

    root.after(1000, tick)  # start after 1s (allow screen to settle)
    root.mainloop()


if __name__ == "__main__":
    main()
