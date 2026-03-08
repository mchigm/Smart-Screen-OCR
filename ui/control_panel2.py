"""
ui/control_panel.py
Premium dark UI — cyberpunk-minimal aesthetic.
Animated scan line, glowing accents, custom widgets, smooth transitions.
"""

from __future__ import annotations
import os
import math
import tkinter as tk
from tkinter import filedialog
from core.pipeline import Pipeline
from utils.logger import setup_logger

logger = setup_logger()

# ── Palette ───────────────────────────────────────────────────────────────────
C = {
    "bg":        "#080c10",
    "bg2":       "#0d1219",
    "surface":   "#111827",
    "surface2":  "#1a2332",
    "border":    "#1e2d3d",
    "border2":   "#243447",
    "cyan":      "#00d4ff",
    "cyan_dim":  "#0099bb",
    "cyan_glow": "#003344",
    "green":     "#00ff88",
    "green_dim": "#00bb66",
    "green_glow":"#003322",
    "yellow":    "#ffcc00",
    "red":       "#ff4455",
    "purple":    "#bb88ff",
    "orange":    "#ff9944",
    "pink":      "#ff66cc",
    "text":      "#ccd6e8",
    "text2":     "#8899aa",
    "muted":     "#445566",
    "white":     "#e8f0f8",
}

LABEL_COLORS = {
    "code snippet": C["cyan"],
    "command":      C["purple"],
    "url":          C["green"],
    "question":     C["orange"],
    "definition":   C["pink"],
    "general note": C["text2"],
    "empty":        C["muted"],
    "error":        C["red"],
    "cancelled":    C["muted"],
}

LABEL_GLOWS = {
    "code snippet": "#003344",
    "command":      "#220033",
    "url":          "#003322",
    "question":     "#331100",
    "definition":   "#330022",
    "general note": "#1a2332",
    "error":        "#330011",
}

F = {
    "title":  ("Consolas", 15, "bold"),
    "head":   ("Consolas", 11, "bold"),
    "body":   ("Consolas", 10),
    "small":  ("Consolas", 9),
    "micro":  ("Consolas", 8),
    "badge":  ("Consolas", 8, "bold"),
    "icon":   ("Consolas", 22),
    "huge":   ("Consolas", 32),
}


class ControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self._current_file: str | None = None
        self._anim_angle    = 0.0
        self._pulse_val     = 0.0
        self._pulse_dir     = 1
        self._scan_y        = 0
        self._working       = False
        self._pipeline = Pipeline(on_result=self._on_result, on_status=self._on_status)
        self._setup_window()
        self._build_ui()
        self._enable_drag_drop()
        self._start_animations()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.title("Smart Screen OCR")
        self.root.geometry("780x700")
        self.root.minsize(700, 600)
        self.root.configure(bg=C["bg"])
        self.root.resizable(True, True)
        # Custom icon via canvas (no .ico file needed)
        self.root.option_add("*Font", ("Consolas", 10))

    # ── Full UI Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        r = self.root

        # ════════════════════════════════════
        # TOP HEADER STRIP
        # ════════════════════════════════════
        self._header = tk.Canvas(r, bg=C["bg"], height=72,
                                  highlightthickness=0)
        self._header.pack(fill="x")
        self._draw_header()

        # Animated top accent line
        self._top_line = tk.Canvas(r, bg=C["bg"], height=2,
                                    highlightthickness=0)
        self._top_line.pack(fill="x")
        self._draw_top_line()

        # ════════════════════════════════════
        # MAIN BODY — two column layout
        # ════════════════════════════════════
        body = tk.Frame(r, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=(14, 0))

        # LEFT PANEL
        left = tk.Frame(body, bg=C["bg"], width=310)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        self._build_left(left)

        # RIGHT PANEL
        right = tk.Frame(body, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

        # ════════════════════════════════════
        # BOTTOM STATUS BAR
        # ════════════════════════════════════
        self._build_statusbar(r)

    # ── Header ────────────────────────────────────────────────────────────────

    def _draw_header(self):
        c = self._header
        c.delete("all")
        w = self.root.winfo_width() or 780

        # Background gradient (simulated with rectangles)
        for i in range(72):
            ratio = i / 72
            r_val = int(8  + ratio * 5)
            g_val = int(12 + ratio * 8)
            b_val = int(16 + ratio * 12)
            color = f"#{r_val:02x}{g_val:02x}{b_val:02x}"
            c.create_rectangle(0, i, w, i+1, fill=color, outline="")

        # Corner bracket accents
        bracket_color = C["cyan"]
        c.create_line(16, 16, 16, 36, fill=bracket_color, width=2)
        c.create_line(16, 16, 32, 16, fill=bracket_color, width=2)
        c.create_line(16, 56, 16, 36, fill=bracket_color, width=1)

        # Logo mark
        c.create_text(46, 36, text="◈", fill=C["cyan"], font=("Consolas", 24, "bold"), anchor="w")

        # Title
        c.create_text(82, 28, text="SMART SCREEN OCR",
                      fill=C["white"], font=("Consolas", 16, "bold"), anchor="w")
        c.create_text(83, 48, text="Contextual Meeting Assistant  ·  v2.0",
                      fill=C["text2"], font=("Consolas", 9), anchor="w")

        # Right side status indicator
        self._status_canvas = c
        self._status_x = w - 20
        self._draw_status_indicator(C["green"], "READY")

        # Right bracket
        c.create_line(w-16, 16, w-16, 36, fill=bracket_color, width=2)
        c.create_line(w-32, 16, w-16, 16, fill=bracket_color, width=2)

    def _draw_status_indicator(self, color, text):
        c = self._status_canvas
        c.delete("status_group")
        w = self.root.winfo_width() or 780
        x = w - 120
        # Glow circle
        c.create_oval(x-5, 31, x+5, 41, fill=color, outline="", tags="status_group")
        c.create_text(x+14, 36, text=text, fill=color,
                      font=("Consolas", 9, "bold"), anchor="w", tags="status_group")

    def _draw_top_line(self):
        c = self._top_line
        c.delete("all")
        w = self.root.winfo_width() or 780
        c.create_rectangle(0, 0, w, 2, fill=C["border2"], outline="")
        # Gradient cyan bar
        for i in range(200):
            alpha = 1.0 - abs(i - 100) / 100
            val = int(alpha * 255)
            color = f"#00{val:02x}{val:02x}" if val > 0 else "#000000"
            c.create_rectangle(i * (w//200), 0, (i+1)*(w//200), 2,
                                fill=C["cyan"] if alpha > 0.7 else C["border2"],
                                outline="")

    # ── LEFT PANEL ────────────────────────────────────────────────────────────

    def _build_left(self, parent):

        # ── Upload zone (canvas for custom border) ────────────────────────────
        tk.Label(parent, text="INPUT IMAGE", bg=C["bg"],
                 fg=C["cyan"], font=F["badge"]).pack(anchor="w", pady=(0, 6))

        self._upload_canvas = tk.Canvas(parent, bg=C["surface"], height=190,
                                         highlightthickness=0, cursor="hand2")
        self._upload_canvas.pack(fill="x")
        self._upload_canvas.bind("<Button-1>", lambda e: self._browse())
        self._upload_canvas.bind("<Enter>",    self._upload_hover_on)
        self._upload_canvas.bind("<Leave>",    self._upload_hover_off)
        self._draw_upload_zone(hover=False)

        # ── File info card ────────────────────────────────────────────────────
        self._file_card = tk.Canvas(parent, bg=C["surface2"], height=52,
                                     highlightthickness=0)
        self._file_card.pack(fill="x", pady=(8, 0))
        self._draw_file_card("No file selected", False)

        # ── Options ───────────────────────────────────────────────────────────
        opts_frame = tk.Frame(parent, bg=C["bg"])
        opts_frame.pack(fill="x", pady=(12, 0))

        self._auto_open_var = tk.BooleanVar(value=True)
        self._cb_frame = tk.Frame(opts_frame, bg=C["surface"],
                                   highlightbackground=C["border"],
                                   highlightthickness=1)
        self._cb_frame.pack(fill="x")

        cb_inner = tk.Frame(self._cb_frame, bg=C["surface"])
        cb_inner.pack(fill="x", padx=12, pady=8)

        self._cb_dot = tk.Label(cb_inner, text="◉", bg=C["surface"],
                                 fg=C["green"], font=("Consolas", 12))
        self._cb_dot.pack(side="left")

        tk.Label(cb_inner, text="  Auto-open in Notepad", bg=C["surface"],
                 fg=C["text"], font=F["small"]).pack(side="left")

        self._cb_frame.bind("<Button-1>", self._toggle_checkbox)
        cb_inner.bind("<Button-1>",       self._toggle_checkbox)
        self._cb_dot.bind("<Button-1>",   self._toggle_checkbox)

        # ── Stats panel ───────────────────────────────────────────────────────
        stats_lbl = tk.Frame(parent, bg=C["bg"])
        stats_lbl.pack(fill="x", pady=(14, 4))
        tk.Label(stats_lbl, text="SESSION STATS", bg=C["bg"],
                 fg=C["cyan"], font=F["badge"]).pack(anchor="w")

        self._stats_canvas = tk.Canvas(parent, bg=C["surface"], height=80,
                                        highlightthickness=0)
        self._stats_canvas.pack(fill="x")
        self._extractions = 0
        self._chars_total  = 0
        self._draw_stats()

        # ── Extract button ────────────────────────────────────────────────────
        btn_frame = tk.Frame(parent, bg=C["bg"])
        btn_frame.pack(fill="x", pady=(16, 0))

        self._extract_btn = tk.Canvas(btn_frame, bg=C["bg"], height=52,
                                       highlightthickness=0, cursor="hand2")
        self._extract_btn.pack(fill="x")
        self._draw_extract_btn(enabled=False)
        self._extract_btn.bind("<Button-1>", lambda e: self._extract())
        self._extract_btn.bind("<Enter>",    self._btn_hover_on)
        self._extract_btn.bind("<Leave>",    self._btn_hover_off)
        self._btn_enabled = False

    def _draw_upload_zone(self, hover=False):
        c = self._upload_canvas
        c.delete("all")
        w = c.winfo_width() or 310
        h = 190

        border_color = C["cyan"] if hover else C["border2"]
        bg_color     = C["surface2"] if hover else C["surface"]

        c.create_rectangle(0, 0, w, h, fill=bg_color, outline="")

        # Dashed border (simulated with segments)
        dash_len, gap_len = 8, 5
        # Top
        x = 0
        while x < w:
            c.create_line(x, 0, min(x+dash_len, w), 0, fill=border_color, width=1)
            x += dash_len + gap_len
        # Bottom
        x = 0
        while x < w:
            c.create_line(x, h-1, min(x+dash_len, w), h-1, fill=border_color, width=1)
            x += dash_len + gap_len
        # Left
        y = 0
        while y < h:
            c.create_line(0, y, 0, min(y+dash_len, h), fill=border_color, width=1)
            y += dash_len + gap_len
        # Right
        y = 0
        while y < h:
            c.create_line(w-1, y, w-1, min(y+dash_len, h), fill=border_color, width=1)
            y += dash_len + gap_len

        # Corner dots
        for cx, cy in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]:
            c.create_oval(cx-3, cy-3, cx+3, cy+3, fill=border_color, outline="")

        # Icon
        icon_color = C["cyan"] if hover else C["text2"]
        c.create_text(w//2, 68, text="⬆", fill=icon_color,
                      font=("Consolas", 30), anchor="center")

        # Text lines
        c.create_text(w//2, 112, text="Drop image or click to browse",
                      fill=C["text"] if hover else C["text2"],
                      font=F["body"], anchor="center")
        c.create_text(w//2, 134, text="PNG  ·  JPG  ·  BMP  ·  TIFF",
                      fill=C["cyan"] if hover else C["muted"],
                      font=F["micro"], anchor="center")

        # Scan line animation placeholder
        if hover:
            c.create_rectangle(0, self._scan_y % h, w, (self._scan_y % h) + 2,
                                fill=C["cyan_glow"], outline="", tags="scan")

    def _draw_file_card(self, filename: str, has_file: bool):
        c = self._file_card
        c.delete("all")
        w = c.winfo_width() or 310

        bg = C["surface2"] if has_file else C["surface"]
        c.create_rectangle(0, 0, w, 52, fill=bg, outline="")

        if has_file:
            c.create_rectangle(0, 0, 3, 52, fill=C["cyan"], outline="")
            c.create_text(16, 18, text="FILE", fill=C["cyan"],
                          font=F["badge"], anchor="w")
            # truncate filename
            display = filename if len(filename) < 32 else "…" + filename[-29:]
            c.create_text(16, 36, text=display, fill=C["white"],
                          font=F["small"], anchor="w")
        else:
            c.create_rectangle(0, 0, 3, 52, fill=C["muted"], outline="")
            c.create_text(16, 26, text="No file selected",
                          fill=C["muted"], font=F["small"], anchor="w")

    def _draw_stats(self):
        c = self._stats_canvas
        c.delete("all")
        w = c.winfo_width() or 310

        c.create_rectangle(0, 0, w, 80, fill=C["surface"], outline="")

        # Two stat boxes
        mid = w // 2
        for i, (label, val, color) in enumerate([
            ("EXTRACTIONS", str(self._extractions), C["cyan"]),
            ("CHARS SAVED",  f"{self._chars_total:,}", C["green"]),
        ]):
            x = i * mid
            c.create_rectangle(x, 0, x+mid-2, 80, fill=C["surface"], outline="")
            if i == 0:
                c.create_rectangle(x, 0, x+2, 80, fill=C["border2"], outline="")
            c.create_text(x + mid//2, 24, text=label, fill=C["muted"],
                          font=F["micro"], anchor="center")
            c.create_text(x + mid//2, 52, text=val, fill=color,
                          font=("Consolas", 18, "bold"), anchor="center")

    def _draw_extract_btn(self, enabled: bool, hover: bool = False):
        c = self._extract_btn
        c.delete("all")
        w = c.winfo_width() or 310

        if not enabled:
            bg     = C["surface"]
            border = C["muted"]
            fg     = C["muted"]
            text   = "▶   EXTRACT TEXT"
        elif hover:
            bg     = C["green"]
            border = C["green"]
            fg     = C["bg"]
            text   = "▶   EXTRACT TEXT"
        else:
            bg     = C["green_glow"]
            border = C["green"]
            fg     = C["green"]
            text   = "▶   EXTRACT TEXT"

        c.create_rectangle(0, 0, w, 52, fill=bg, outline="")
        # Border
        c.create_rectangle(0, 0, w-1, 51, fill="", outline=border)
        # Corner brackets
        for bx, by, dx, dy in [(0,0,12,0),(0,0,0,12),(w-1,0,-12,0),(w-1,0,0,12),
                                (0,51,12,0),(0,51,0,-12),(w-1,51,-12,0),(w-1,51,0,-12)]:
            c.create_line(bx, by, bx+dx, by+dy, fill=border, width=2)

        c.create_text(w//2, 26, text=text, fill=fg,
                      font=("Consolas", 11, "bold"), anchor="center")

    # ── RIGHT PANEL ───────────────────────────────────────────────────────────

    def _build_right(self, parent):

        # Header row
        result_hdr = tk.Frame(parent, bg=C["bg"])
        result_hdr.pack(fill="x", pady=(0, 6))

        tk.Label(result_hdr, text="EXTRACTED TEXT", bg=C["bg"],
                 fg=C["cyan"], font=F["badge"]).pack(side="left")

        self._badge_canvas = tk.Canvas(result_hdr, bg=C["bg"], width=160, height=22,
                                        highlightthickness=0)
        self._badge_canvas.pack(side="left", padx=(10, 0))
        self._draw_badge("", C["muted"])

        self._folder_btn = tk.Label(result_hdr, text="📂 outputs/", bg=C["bg"],
                                     fg=C["muted"], font=F["small"], cursor="hand2")
        self._folder_btn.pack(side="right")
        self._folder_btn.bind("<Button-1>", self._open_output_folder)

        # Text box with custom styled frame
        text_wrap = tk.Canvas(parent, bg=C["border"], highlightthickness=0)
        text_wrap.pack(fill="both", expand=True)

        text_inner = tk.Frame(text_wrap, bg=C["surface"], padx=1, pady=1)
        text_wrap.create_window(0, 0, anchor="nw", window=text_inner,
                                  width=text_wrap.winfo_width(),
                                  height=text_wrap.winfo_height())
        text_wrap.bind("<Configure>", lambda e: text_wrap.itemconfig(
            text_wrap.find_all()[0] if text_wrap.find_all() else 1,
            width=e.width, height=e.height
        ))

        # Line number gutter
        gutter_frame = tk.Frame(text_inner, bg=C["surface2"], width=36)
        gutter_frame.pack(side="left", fill="y")
        gutter_frame.pack_propagate(False)

        self._gutter = tk.Text(
            gutter_frame,
            bg=C["surface2"], fg=C["muted"],
            font=F["small"],
            width=4, relief="flat", bd=0,
            padx=4, pady=14,
            state="disabled",
            cursor="arrow"
        )
        self._gutter.pack(fill="both", expand=True)

        # Main text area
        text_frame = tk.Frame(text_inner, bg=C["surface"])
        text_frame.pack(side="left", fill="both", expand=True)

        self._text_box = tk.Text(
            text_frame,
            bg=C["surface"], fg=C["text"],
            insertbackground=C["cyan"],
            selectbackground=C["cyan_glow"],
            selectforeground=C["cyan"],
            font=F["body"],
            relief="flat", bd=0,
            wrap="none",
            padx=14, pady=14,
            state="disabled",
            cursor="arrow"
        )

        # Scrollbars
        v_scroll = tk.Scrollbar(text_frame, orient="vertical",
                                  command=self._sync_scroll,
                                  bg=C["surface2"], troughcolor=C["surface"],
                                  activebackground=C["border2"],
                                  relief="flat", bd=0, width=10)
        h_scroll = tk.Scrollbar(text_inner, orient="horizontal",
                                  command=self._text_box.xview,
                                  bg=C["surface2"], troughcolor=C["surface"],
                                  relief="flat", bd=0)

        self._text_box.config(yscrollcommand=v_scroll.set,
                               xscrollcommand=h_scroll.set)

        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        self._text_box.pack(fill="both", expand=True)

        # Progress bar
        self._prog_canvas = tk.Canvas(parent, bg=C["bg"], height=4,
                                       highlightthickness=0)
        self._prog_canvas.pack(fill="x", pady=(6, 0))
        self._prog_w = 0

    def _draw_badge(self, label: str, color: str):
        c = self._badge_canvas
        c.delete("all")
        if not label:
            return
        text = f"  {label.upper()}  "
        c.create_rectangle(0, 0, 160, 22, fill=LABEL_GLOWS.get(label, C["surface2"]), outline="")
        c.create_rectangle(0, 0, 159, 21, fill="", outline=color)
        c.create_rectangle(0, 0, 3, 22, fill=color, outline="")
        c.create_text(82, 11, text=text, fill=color,
                      font=F["badge"], anchor="center")

    def _sync_scroll(self, *args):
        self._text_box.yview(*args)
        self._update_gutter()

    def _update_gutter(self):
        self._gutter.config(state="normal")
        self._gutter.delete("1.0", "end")
        content = self._text_box.get("1.0", "end-1c")
        lines = content.count("\n") + 1 if content.strip() else 0
        nums = "\n".join(str(i+1) for i in range(lines))
        self._gutter.insert("1.0", nums)
        self._gutter.config(state="disabled")

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_statusbar(self, parent):
        bar = tk.Canvas(parent, bg=C["bg2"], height=30, highlightthickness=0)
        bar.pack(fill="x", side="bottom")

        # Top edge
        bar.create_rectangle(0, 0, 2000, 1, fill=C["border"], outline="")

        self._status_bar = bar
        self._status_text_id = bar.create_text(
            16, 15, text="◈  Ready — upload an image to begin.",
            fill=C["text2"], font=F["small"], anchor="w"
        )
        bar.create_text(
            764, 15, text="outputs/  ·  logs/app.log",
            fill=C["muted"], font=F["micro"], anchor="e"
        )

    def _set_status_bar(self, text: str, color: str = None):
        self._status_bar.itemconfig(
            self._status_text_id,
            text=f"◈  {text}",
            fill=color or C["text2"]
        )

    # ── Animations ────────────────────────────────────────────────────────────

    def _start_animations(self):
        self._animate_pulse()
        self._animate_progress()

    def _animate_pulse(self):
        """Pulse the status dot and scan the upload zone."""
        self._pulse_val += 0.08 * self._pulse_dir
        if self._pulse_val >= 1.0:
            self._pulse_dir = -1
        elif self._pulse_val <= 0.0:
            self._pulse_dir = 1

        self._scan_y = (self._scan_y + 2) % 190

        if self._working:
            # Animate scan line over upload zone
            c = self._upload_canvas
            c.delete("scan")
            w = c.winfo_width() or 310
            y = self._scan_y
            c.create_rectangle(0, y, w, y+2, fill="#001a22", outline="", tags="scan")
            c.create_rectangle(0, y, w, y+1, fill=C["cyan_dim"], outline="", tags="scan")

        self.root.after(40, self._animate_pulse)

    def _animate_progress(self):
        """Animate progress bar while working."""
        if self._working:
            self._prog_w = (self._prog_w + 3) % (self._prog_canvas.winfo_width() or 440)
            c = self._prog_canvas
            c.delete("all")
            w = c.winfo_width() or 440
            c.create_rectangle(0, 0, w, 4, fill=C["surface"], outline="")
            # Moving gradient bar
            bar_w = 120
            x = self._prog_w
            for i in range(bar_w):
                ratio = 1.0 - abs(i - bar_w//2) / (bar_w//2)
                val = int(ratio * 255)
                col = f"#00{val:02x}ff" if val < 16 else f"#00d4{val:02x}"
                px = (x - bar_w//2 + i) % w
                c.create_rectangle(px, 0, px+2, 4, fill=C["cyan"], outline="")
        else:
            c = self._prog_canvas
            c.delete("all")
            w = c.winfo_width() or 440
            c.create_rectangle(0, 0, w, 4, fill=C["surface"], outline="")

        self.root.after(20, self._animate_progress)

    # ── Hover effects ─────────────────────────────────────────────────────────

    def _upload_hover_on(self, e=None):
        self._draw_upload_zone(hover=True)

    def _upload_hover_off(self, e=None):
        self._draw_upload_zone(hover=False)

    def _btn_hover_on(self, e=None):
        if self._btn_enabled:
            self._draw_extract_btn(enabled=True, hover=True)

    def _btn_hover_off(self, e=None):
        if self._btn_enabled:
            self._draw_extract_btn(enabled=True, hover=False)

    # ── Toggle checkbox ───────────────────────────────────────────────────────

    def _toggle_checkbox(self, e=None):
        self._auto_open_var.set(not self._auto_open_var.get())
        dot = "◉" if self._auto_open_var.get() else "◎"
        color = C["green"] if self._auto_open_var.get() else C["muted"]
        self._cb_dot.config(text=dot, fg=color)

    # ── Drag & Drop ───────────────────────────────────────────────────────────

    def _enable_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)
            logger.info("Drag-and-drop enabled.")
        except Exception:
            logger.info("tkinterdnd2 not found — browse still works.")

    def _on_drop(self, event):
        path = event.data.strip().strip("{}")
        if os.path.isfile(path):
            self._load_file(path)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select Screenshot",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                       ("All files", "*.*")]
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        self._current_file = path
        short = os.path.basename(path)
        self._draw_file_card(short, True)
        self._btn_enabled = True
        self._draw_extract_btn(enabled=True)
        self._set_status_bar(f"Loaded: {short}", C["cyan"])
        self._update_text_box("")
        self._draw_badge("", C["muted"])
        self._folder_btn.config(fg=C["muted"])
        self._draw_header()

    def _extract(self):
        if not self._current_file or not self._btn_enabled:
            return
        self._working = True
        self._btn_enabled = False
        self._draw_extract_btn(enabled=False)
        self._draw_status_indicator(C["yellow"], "WORKING")
        self._set_status_bar("Processing image…", C["yellow"])
        self._draw_badge("working", C["yellow"])
        self._update_text_box("")

        self._pipeline.run(
            image_path=self._current_file,
            auto_open_notepad=self._auto_open_var.get()
        )

    # ── Pipeline callbacks ────────────────────────────────────────────────────

    def _on_status(self, msg: str):
        self.root.after(0, self._set_status_bar, msg, C["yellow"])

    def _on_result(self, result: dict):
        self.root.after(0, self._apply_result, result)

    def _apply_result(self, result: dict):
        self._working = False
        status = result.get("status", "error")

        if status == "success":
            label    = result.get("label", "general note")
            text     = result.get("text", "")
            filepath = result.get("filepath", "")
            score    = result.get("score", 0)
            color    = LABEL_COLORS.get(label, C["text2"])

            self._draw_badge(label, color)
            self._update_text_box(text)
            self._folder_btn.config(
                text=f"📂  {os.path.basename(filepath)}",
                fg=C["cyan"]
            )
            self._set_status_bar(f"✔  Saved → {os.path.basename(filepath)}", C["green"])
            self._draw_status_indicator(C["green"], "DONE")

            self._extractions += 1
            self._chars_total  += len(text)
            self._draw_stats()

        elif status == "empty":
            self._draw_badge("empty", C["yellow"])
            self._update_text_box(
                "⚠  No text detected in this image.\n\n"
                "Tips:\n"
                "  ·  Make sure the image contains readable text\n"
                "  ·  Try a higher-resolution screenshot\n"
                "  ·  Avoid stylised or handwritten fonts\n"
                "  ·  Increase UPSCALE_FACTOR in config.py"
            )
            self._set_status_bar("No text detected.", C["yellow"])
            self._draw_status_indicator(C["yellow"], "EMPTY")

        elif status == "error":
            msg = result.get("message", "Unknown error")
            self._draw_badge("error", C["red"])
            self._update_text_box(f"✖  Error:\n\n{msg}")
            self._set_status_bar(f"Error: {msg[:60]}", C["red"])
            self._draw_status_indicator(C["red"], "ERROR")

        self._btn_enabled = True
        self._draw_extract_btn(enabled=True)

    # ── Text box ──────────────────────────────────────────────────────────────

    def _update_text_box(self, text: str):
        self._text_box.config(state="normal")
        self._text_box.delete("1.0", "end")
        if text:
            self._text_box.insert("1.0", text)
        self._text_box.config(state="disabled")
        self._update_gutter()

    def _open_output_folder(self, e=None):
        import subprocess
        folder = os.path.abspath("outputs")
        os.makedirs(folder, exist_ok=True)
        try:
            subprocess.Popen(f'explorer "{folder}"')
        except Exception:
            pass

    def run(self):
        self.root.mainloop()