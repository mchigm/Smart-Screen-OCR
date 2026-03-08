"""
ui/control_panel.py  — v5
Layout: top toolbar + bottom notebook tabs for settings, no vertical clipping.
All features visible at any reasonable screen size.
"""
from __future__ import annotations
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

from core.pipeline        import Pipeline
from core.history_manager import load_all, clear_all
from core.ocr_engine      import _strategy_dark_code
from utils.logger         import setup_logger

logger = setup_logger()

# ── Palette ───────────────────────────────────────────────────────────────────
C = {
    "bg":        "#080c10", "bg2":       "#0d1219",
    "surface":   "#111827", "surface2":  "#1a2332",
    "border":    "#1e2d3d", "border2":   "#243447",
    "cyan":      "#00d4ff", "cyan_glow": "#002233",
    "green":     "#00ff88", "green_glow":"#003322",
    "yellow":    "#ffcc00", "red":       "#ff4455",
    "purple":    "#bb88ff", "orange":    "#ff9944",
    "pink":      "#ff66cc", "text":      "#ccd6e8",
    "text2":     "#8899aa", "muted":     "#445566",
    "white":     "#e8f0f8",
}
LABEL_COLORS = {
    "code snippet":"#00d4ff","command":"#bb88ff","url":"#00ff88",
    "question":"#ff9944","definition":"#ff66cc","general note":"#8899aa",
    "empty":"#445566","error":"#ff4455","cancelled":"#445566","working":"#ffcc00",
}
LABEL_GLOWS = {
    "code snippet":"#002233","command":"#220033","url":"#003322",
    "question":"#331100","definition":"#330022",
    "general note":"#1a2332","error":"#330011",
}
F = {
    "head":  ("Consolas", 11, "bold"),
    "body":  ("Consolas", 10),
    "small": ("Consolas", 9),
    "micro": ("Consolas", 8),
    "badge": ("Consolas", 8, "bold"),
}
LANGS = [
    ("English","eng"),("Hindi","hin"),("French","fra"),("German","deu"),
    ("Spanish","spa"),("Arabic","ara"),("Chinese Sim.","chi_sim"),("Japanese","jpn"),
]


# ══════════════════════════════════════════════════════════════════════════════
class ControlPanel:
# ══════════════════════════════════════════════════════════════════════════════

    def __init__(self):
        self.root = tk.Tk()
        self._file         : str | None = None
        self._batch_files  : list       = []
        self._batch_idx    : int        = 0
        self._is_batch     : bool       = False
        self._working      : bool       = False
        self._btn_enabled  : bool       = False
        self._prog_w       : int        = 0
        self._scan_y       : int        = 0
        self._raw_pil      = None
        self._proc_pil     = None
        self._show_proc    : bool       = False
        self._current_photo             = None

        self._pipeline = Pipeline(
            on_result=self._on_result,
            on_status=self._on_status,
        )
        self._setup_window()
        self._build_ui()
        self._bind_shortcuts()
        self._enable_drag_drop()
        self._start_animations()
        self._refresh_history()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.title("Smart Screen OCR")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(bg=C["bg"])
        self.root.resizable(True, True)

    def _bind_shortcuts(self):
        self.root.bind("<Control-o>",      lambda e: self._browse())
        self.root.bind("<Control-O>",      lambda e: self._browse())
        self.root.bind("<Control-Return>", lambda e: self._extract())
        self.root.bind("<Control-k>",      lambda e: self._copy_text())
        self.root.bind("<Control-K>",      lambda e: self._copy_text())
        self.root.bind("<Control-r>",      lambda e: self._reset())
        self.root.bind("<Control-R>",      lambda e: self._reset())
        self.root.bind("<Escape>",         lambda e: self._reset())

    # ══════════════════════════════════════════════════════════════════════════
    # LAYOUT  ──  header / toolbar / [left result | right tabs]
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        r = self.root

        # 1 ── Header strip
        self._hdr = tk.Canvas(r, bg=C["bg"], height=60, highlightthickness=0)
        self._hdr.pack(fill="x")
        self._hdr.bind("<Configure>", lambda e: self._draw_header())
        tk.Canvas(r, bg=C["border"], height=1, highlightthickness=0).pack(fill="x")

        # 2 ── Toolbar  (file + extract + action buttons all in one row)
        self._build_toolbar(r)
        tk.Canvas(r, bg=C["border"], height=1, highlightthickness=0).pack(fill="x")

        # 3 ── Middle: result pane (left, expands) + settings notebook (right, fixed)
        mid = tk.Frame(r, bg=C["bg"])
        mid.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        result_pane = tk.Frame(mid, bg=C["bg"])
        result_pane.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._build_result_pane(result_pane)

        right_pane = tk.Frame(mid, bg=C["bg"], width=310)
        right_pane.pack(side="left", fill="y")
        right_pane.pack_propagate(False)
        self._build_right_notebook(right_pane)

        # 4 ── Status bar
        self._build_statusbar(r)

    # ══════════════════════════════════════════════════════════════════════════
    # TOOLBAR  — one horizontal strip, nothing gets stacked vertically
    # ══════════════════════════════════════════════════════════════════════════

    def _build_toolbar(self, parent):
        tb = tk.Frame(parent, bg=C["surface"], height=52)
        tb.pack(fill="x")
        tb.pack_propagate(False)

        inner = tk.Frame(tb, bg=C["surface"])
        inner.pack(fill="both", expand=True, padx=12, pady=6)

        # ── Upload zone (click area)
        self._upload_btn = tk.Canvas(inner, bg=C["bg2"], width=180, height=40,
                                      highlightthickness=0, cursor="hand2")
        self._upload_btn.pack(side="left", padx=(0, 6))
        self._draw_upload_btn()
        self._upload_btn.bind("<Button-1>", lambda e: self._browse())
        self._upload_btn.bind("<Enter>",    lambda e: self._draw_upload_btn(True))
        self._upload_btn.bind("<Leave>",    lambda e: self._draw_upload_btn(False))

        # ── File name label
        self._file_lbl = tk.Label(inner, text="No file selected",
                                   bg=C["surface"], fg=C["muted"],
                                   font=F["small"], anchor="w")
        self._file_lbl.pack(side="left", padx=(0, 16), fill="x")

        # ── Batch button
        batch_c = tk.Canvas(inner, bg=C["surface"], width=120, height=40,
                             highlightthickness=0, cursor="hand2")
        batch_c.pack(side="left", padx=(0, 16))
        self._draw_flat_btn(batch_c, "⊞  Batch Folder", C["purple"])
        batch_c.bind("<Button-1>", lambda e: self._browse_batch())

        # ── Separator
        tk.Frame(inner, bg=C["border2"], width=1).pack(side="left", fill="y", padx=(0,16))

        # ── Extract button
        self._ext_canvas = tk.Canvas(inner, bg=C["surface"], width=160, height=40,
                                      highlightthickness=0, cursor="hand2")
        self._ext_canvas.pack(side="left", padx=(0, 8))
        self._draw_ext_btn(False)
        self._ext_canvas.bind("<Button-1>", lambda e: self._extract())
        self._ext_canvas.bind("<Enter>",    lambda e: self._ext_hover(True))
        self._ext_canvas.bind("<Leave>",    lambda e: self._ext_hover(False))

        # ── Action buttons (right side)
        self._copy_btn   = self._toolbar_btn(inner, "⎘ Copy",    C["cyan"],   self._copy_text)
        self._clear_btn  = self._toolbar_btn(inner, "✕ Clear",   C["muted"],  self._reset)
        self._folder_btn = self._toolbar_btn(inner, "📂 Outputs", C["text2"],  self._open_outputs)

        # ── Batch progress label (far right)
        self._batch_lbl = tk.Label(inner, text="", bg=C["surface"],
                                    fg=C["yellow"], font=F["micro"])
        self._batch_lbl.pack(side="right", padx=8)

    def _draw_upload_btn(self, hover=False):
        c = self._upload_btn
        c.delete("all")
        bg  = C["border2"] if hover else C["bg2"]
        fg  = C["cyan"]    if hover else C["text2"]
        bdr = C["cyan"]    if hover else C["border"]
        c.create_rectangle(0, 0, 179, 39, fill=bg, outline=bdr)
        c.create_text(90, 20, text="⬆  Browse / Drop Image",
                       fill=fg, font=F["small"], anchor="center")

    def _draw_ext_btn(self, enabled, hover=False):
        c = self._ext_canvas
        c.delete("all")
        w, h = 160, 40
        if not enabled:
            bg, bdr, fg = C["surface"], C["muted"],  C["muted"]
        elif hover:
            bg, bdr, fg = C["green"],   C["green"],  C["bg"]
        else:
            bg, bdr, fg = C["green_glow"], C["green"], C["green"]
        c.create_rectangle(0, 0, w, h, fill=bg, outline="")
        c.create_rectangle(0, 0, w-1, h-1, fill="", outline=bdr)
        for bx,by,dx,dy in [(0,0,8,0),(0,0,0,8),(w-1,0,-8,0),(w-1,0,0,8),
                             (0,h-1,8,0),(0,h-1,0,-8),(w-1,h-1,-8,0),(w-1,h-1,0,-8)]:
            c.create_line(bx, by, bx+dx, by+dy, fill=bdr, width=2)
        c.create_text(w//2, h//2, text="▶  EXTRACT TEXT",
                       fill=fg, font=("Consolas", 10, "bold"), anchor="center")

    def _draw_flat_btn(self, c, text, color):
        c.delete("all")
        w = c.winfo_width()  or int(c["width"])  or 120
        h = c.winfo_height() or int(c["height"]) or 40
        c.create_rectangle(0, 0, w, h,   fill=C["surface"], outline="")
        c.create_rectangle(0, 0, w-1, h-1, fill="", outline=color)
        c.create_text(w//2, h//2, text=text, fill=color,
                       font=("Consolas", 9, "bold"), anchor="center")

    def _toolbar_btn(self, parent, text, color, cmd):
        b = tk.Label(parent, text=text, bg=C["surface2"], fg=color,
                      font=F["micro"], cursor="hand2", padx=8, pady=4)
        b.pack(side="left", padx=(0, 4))
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>",    lambda e: b.config(bg=C["border2"]))
        b.bind("<Leave>",    lambda e: b.config(bg=C["surface2"]))
        return b

    # ══════════════════════════════════════════════════════════════════════════
    # RESULT PANE  (centre-left)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_result_pane(self, p):
        # Badge row
        badge_row = tk.Frame(p, bg=C["bg"])
        badge_row.pack(fill="x", pady=(0, 6))
        tk.Label(badge_row, text="EXTRACTED TEXT",
                 bg=C["bg"], fg=C["cyan"], font=F["badge"]).pack(side="left")
        self._badge_c = tk.Canvas(badge_row, bg=C["bg"], width=160, height=20,
                                   highlightthickness=0)
        self._badge_c.pack(side="left", padx=(8, 0))
        self._draw_badge("", C["muted"])

        # Text area + gutter
        wrap = tk.Frame(p, bg=C["border"], padx=1, pady=1)
        wrap.pack(fill="both", expand=True)
        inner = tk.Frame(wrap, bg=C["surface"])
        inner.pack(fill="both", expand=True)

        gut = tk.Frame(inner, bg=C["surface2"], width=36)
        gut.pack(side="left", fill="y")
        gut.pack_propagate(False)
        self._gutter = tk.Text(gut, bg=C["surface2"], fg=C["muted"],
                                font=F["small"], width=4, relief="flat", bd=0,
                                padx=4, pady=12, state="disabled", cursor="arrow")
        self._gutter.pack(fill="both", expand=True)

        txt_f = tk.Frame(inner, bg=C["surface"])
        txt_f.pack(side="left", fill="both", expand=True)
        self._text_box = tk.Text(
            txt_f, bg=C["surface"], fg=C["text"],
            insertbackground=C["cyan"],
            selectbackground=C["cyan_glow"], selectforeground=C["cyan"],
            font=F["body"], relief="flat", bd=0,
            wrap="none", padx=12, pady=12,
            state="disabled", cursor="arrow",
        )
        vsc = tk.Scrollbar(txt_f, orient="vertical", command=self._vsync,
                            bg=C["surface2"], troughcolor=C["surface"],
                            relief="flat", bd=0, width=8)
        hsc = tk.Scrollbar(inner, orient="horizontal",
                            command=self._text_box.xview,
                            bg=C["surface2"], troughcolor=C["surface"],
                            relief="flat", bd=0)
        self._text_box.config(yscrollcommand=vsc.set, xscrollcommand=hsc.set)
        hsc.pack(side="bottom", fill="x")
        vsc.pack(side="right",  fill="y")
        self._text_box.pack(fill="both", expand=True)

        # Progress bar
        self._prog_c = tk.Canvas(p, bg=C["bg"], height=3, highlightthickness=0)
        self._prog_c.pack(fill="x", pady=(4, 0))

    # ══════════════════════════════════════════════════════════════════════════
    # RIGHT NOTEBOOK  — Settings | History | Preview
    # ══════════════════════════════════════════════════════════════════════════

    def _build_right_notebook(self, p):
        # Tab buttons
        tab_bar = tk.Frame(p, bg=C["bg2"])
        tab_bar.pack(fill="x")
        tk.Canvas(tab_bar, bg=C["border"], height=1,
                   highlightthickness=0).pack(fill="x", side="bottom")

        self._tab_btns   = {}
        self._tab_frames = {}

        for name, label in [("settings", "⚙ Settings"),
                             ("history",  "📋 History"),
                             ("preview",  "🖼 Preview")]:
            b = tk.Label(tab_bar, text=label, bg=C["bg2"], fg=C["muted"],
                          font=F["micro"], cursor="hand2", padx=10, pady=5)
            b.pack(side="left")
            b.bind("<Button-1>", lambda e, n=name: self._switch_tab(n))
            self._tab_btns[name] = b

        # Content area
        self._tab_area = tk.Frame(p, bg=C["bg"])
        self._tab_area.pack(fill="both", expand=True, pady=(6, 0))

        self._build_settings_tab()
        self._build_history_tab()
        self._build_preview_tab()
        self._switch_tab("settings")

    def _switch_tab(self, name):
        for n, f in self._tab_frames.items():
            if n == name: f.pack(fill="both", expand=True)
            else:         f.pack_forget()
        for n, b in self._tab_btns.items():
            b.config(fg=C["cyan"]  if n == name else C["muted"],
                     bg=C["surface2"] if n == name else C["bg2"])

    # ── Settings tab ──────────────────────────────────────────────────────────

    def _build_settings_tab(self):
        f = tk.Frame(self._tab_area, bg=C["bg"])
        self._tab_frames["settings"] = f

        def row(label):
            tk.Label(f, text=label, bg=C["bg"],
                     fg=C["cyan"], font=F["badge"]).pack(anchor="w", pady=(10,3), padx=2)

        # Export format
        row("▸ EXPORT FORMAT")
        fmt_f = tk.Frame(f, bg=C["surface"],
                          highlightbackground=C["border"], highlightthickness=1)
        fmt_f.pack(fill="x", padx=2)
        self._fmt_var  = tk.StringVar(value="txt")
        self._fmt_btns = []
        for fmt, lbl in [("txt","  TXT  "),("md","  Markdown  "),("clipboard","  Clipboard  ")]:
            b = tk.Label(fmt_f, text=lbl, bg=C["surface"], fg=C["muted"],
                          font=F["small"], cursor="hand2", padx=4, pady=5)
            b.pack(side="left")
            b.bind("<Button-1>", lambda e, ff=fmt, bb=b: self._set_fmt(ff, bb))
            self._fmt_btns.append(b)
        self._set_fmt("txt", self._fmt_btns[0])

        # OCR language
        row("▸ OCR LANGUAGE")
        lang_f = tk.Frame(f, bg=C["surface"],
                           highlightbackground=C["border"], highlightthickness=1)
        lang_f.pack(fill="x", padx=2)
        li = tk.Frame(lang_f, bg=C["surface"])
        li.pack(fill="x", padx=8, pady=5)
        tk.Label(li, text="🌐", bg=C["surface"],
                 fg=C["cyan"], font=("Consolas", 10)).pack(side="left")
        self._lang_var = tk.StringVar(value="English")
        om = tk.OptionMenu(li, self._lang_var, *[n for n, _ in LANGS])
        om.config(bg=C["surface"], fg=C["text"], font=F["small"],
                   activebackground=C["border2"], activeforeground=C["cyan"],
                   relief="flat", bd=0, highlightthickness=0,
                   indicatoron=0, cursor="hand2", width=14)
        om["menu"].config(bg=C["surface2"], fg=C["text"], font=F["small"],
                           activebackground=C["cyan_glow"], activeforeground=C["cyan"])
        om.pack(side="left", padx=6)

        # NLP confidence
        row("▸ NLP CONFIDENCE THRESHOLD")
        conf_f = tk.Frame(f, bg=C["surface"],
                           highlightbackground=C["border"], highlightthickness=1)
        conf_f.pack(fill="x", padx=2)
        ci = tk.Frame(conf_f, bg=C["surface"])
        ci.pack(fill="x", padx=8, pady=6)
        self._conf_var   = tk.DoubleVar(value=0.45)
        self._conf_label = tk.Label(ci, text="0.45", bg=C["surface"],
                                     fg=C["cyan"], font=F["badge"], width=4)
        self._conf_label.pack(side="right")
        tk.Scale(
            ci, from_=0.1, to=0.9, resolution=0.05, orient="horizontal",
            variable=self._conf_var, bg=C["surface"], fg=C["text"],
            troughcolor=C["border2"], activebackground=C["cyan"],
            highlightthickness=0, relief="flat", bd=0,
            showvalue=0, sliderlength=12,
            command=lambda v: self._conf_label.config(text=f"{float(v):.2f}")
        ).pack(side="left", fill="x", expand=True)

        # Options
        row("▸ OPTIONS")
        self._auto_open_var = tk.BooleanVar(value=True)
        self._make_toggle(f, "Auto-open in Notepad", self._auto_open_var)

        # Keyboard shortcuts reference
        row("▸ KEYBOARD SHORTCUTS")
        sc_f = tk.Frame(f, bg=C["surface"],
                         highlightbackground=C["border"], highlightthickness=1)
        sc_f.pack(fill="x", padx=2)
        for key, desc in [("Ctrl+O",   "Open file"),
                           ("Ctrl+↵",  "Extract text"),
                           ("Ctrl+K",  "Copy to clipboard"),
                           ("Ctrl+R",  "Reset / clear"),
                           ("Esc",     "Clear")]:
            row_f = tk.Frame(sc_f, bg=C["surface"])
            row_f.pack(fill="x", padx=8, pady=1)
            tk.Label(row_f, text=f" {key} ", bg=C["surface2"], fg=C["cyan"],
                     font=F["micro"], padx=3).pack(side="left")
            tk.Label(row_f, text=f"  {desc}", bg=C["surface"],
                     fg=C["text2"], font=F["micro"]).pack(side="left")
        tk.Frame(sc_f, bg=C["surface"], height=4).pack()

    # ── History tab ───────────────────────────────────────────────────────────

    def _build_history_tab(self):
        f = tk.Frame(self._tab_area, bg=C["bg"])
        self._tab_frames["history"] = f

        top = tk.Frame(f, bg=C["bg"])
        top.pack(fill="x", pady=(0, 4))
        tk.Label(top, text="EXTRACTION HISTORY", bg=C["bg"],
                 fg=C["cyan"], font=F["badge"]).pack(side="left")
        clr = tk.Label(top, text="🗑 Clear", bg=C["bg"],
                        fg=C["red"], font=F["micro"], cursor="hand2")
        clr.pack(side="right")
        clr.bind("<Button-1>", lambda e: self._clear_history())

        wrap = tk.Frame(f, bg=C["border"], padx=1, pady=1)
        wrap.pack(fill="both", expand=True)
        inner = tk.Frame(wrap, bg=C["surface"])
        inner.pack(fill="both", expand=True)

        self._hist_c = tk.Canvas(inner, bg=C["surface"], highlightthickness=0)
        sc = tk.Scrollbar(inner, orient="vertical", command=self._hist_c.yview,
                           bg=C["surface2"], troughcolor=C["surface"],
                           relief="flat", bd=0, width=6)
        self._hist_c.config(yscrollcommand=sc.set)
        sc.pack(side="right", fill="y")
        self._hist_c.pack(fill="both", expand=True)

        self._hist_inner = tk.Frame(self._hist_c, bg=C["surface"])
        _win = self._hist_c.create_window((0, 0), window=self._hist_inner, anchor="nw")

        def _cfg(e):
            self._hist_c.config(scrollregion=self._hist_c.bbox("all"))
            self._hist_c.itemconfig(_win, width=self._hist_c.winfo_width())
        self._hist_inner.bind("<Configure>", _cfg)
        self._hist_c.bind("<Configure>",
                           lambda e: self._hist_c.itemconfig(_win, width=e.width))

    # ── Preview tab ───────────────────────────────────────────────────────────

    def _build_preview_tab(self):
        f = tk.Frame(self._tab_area, bg=C["bg"])
        self._tab_frames["preview"] = f

        top = tk.Frame(f, bg=C["bg"])
        top.pack(fill="x", pady=(0, 6))
        tk.Label(top, text="IMAGE PREVIEW", bg=C["bg"],
                 fg=C["cyan"], font=F["badge"]).pack(side="left")
        self._proc_btn = tk.Label(top, text="[ processed ]", bg=C["bg"],
                                   fg=C["muted"], font=F["micro"], cursor="hand2")
        self._proc_btn.pack(side="right")
        self._proc_btn.bind("<Button-1>", lambda e: self._toggle_proc())

        self._prev_c = tk.Canvas(f, bg=C["surface"], highlightthickness=0)
        self._prev_c.pack(fill="both", expand=True)
        self._prev_c.bind("<Configure>", lambda e: self._render_preview())
        self._draw_prev_placeholder()

    # ══════════════════════════════════════════════════════════════════════════
    # STATUS BAR
    # ══════════════════════════════════════════════════════════════════════════

    def _build_statusbar(self, parent):
        bar = tk.Canvas(parent, bg=C["bg2"], height=26, highlightthickness=0)
        bar.pack(fill="x", side="bottom")
        bar.create_rectangle(0, 0, 3000, 1, fill=C["border"], outline="")
        self._sbar     = bar
        self._sbar_txt = bar.create_text(
            14, 13, text="◈  Ready — upload an image to begin.",
            fill=C["text2"], font=F["small"], anchor="w"
        )

    def _set_status(self, txt, color=None):
        self._sbar.itemconfig(self._sbar_txt,
                               text=f"◈  {txt}",
                               fill=color or C["text2"])

    # ══════════════════════════════════════════════════════════════════════════
    # CANVAS DRAWS
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_header(self):
        c = self._hdr
        c.delete("all")
        w = c.winfo_width() or 1100
        for i in range(60):
            rv = int(8  + (i/60)*6)
            gv = int(12 + (i/60)*10)
            bv = int(16 + (i/60)*14)
            c.create_rectangle(0, i, w, i+1,
                                fill=f"#{rv:02x}{gv:02x}{bv:02x}", outline="")
        bc = C["cyan"]
        c.create_line(14, 12, 14, 28, fill=bc, width=2)
        c.create_line(14, 12, 26, 12, fill=bc, width=2)
        c.create_text(42, 30, text="◈", fill=C["cyan"],
                       font=("Consolas", 20, "bold"), anchor="w")
        c.create_text(74, 20, text="SMART SCREEN OCR",
                       fill=C["white"], font=("Consolas", 14, "bold"), anchor="w")
        c.create_text(75, 40, text="Contextual Meeting Assistant  ·  v5.0  ·  All Features",
                       fill=C["text2"], font=("Consolas", 8), anchor="w")
        c.create_line(w-14, 12, w-14, 28, fill=bc, width=2)
        c.create_line(w-26, 12, w-14, 12, fill=bc, width=2)
        self._status_canvas = c
        self._draw_status_dot(C["green"], "READY")

    def _draw_status_dot(self, color, text):
        c = self._status_canvas
        c.delete("sdot")
        w = c.winfo_width() or 1100
        x = w - 130
        c.create_oval(x-4, 26, x+4, 34, fill=color, outline="", tags="sdot")
        c.create_text(x+12, 30, text=text, fill=color,
                       font=("Consolas", 9, "bold"), anchor="w", tags="sdot")

    def _draw_badge(self, label, color):
        c = self._badge_c
        c.delete("all")
        if not label:
            return
        c.create_rectangle(0, 0, 160, 20,
                            fill=LABEL_GLOWS.get(label, C["surface2"]), outline="")
        c.create_rectangle(0, 0, 159, 19, fill="", outline=color)
        c.create_rectangle(0, 0, 3, 20, fill=color, outline="")
        c.create_text(82, 10, text=f"  {label.upper()}  ",
                       fill=color, font=F["badge"], anchor="center")

    def _draw_prev_placeholder(self):
        c = self._prev_c
        c.delete("all")
        w = max(c.winfo_width(), 10)
        h = max(c.winfo_height(), 10)
        c.create_rectangle(0, 0, w, h, fill=C["surface"], outline="")
        c.create_text(w//2, h//2, text="No image loaded",
                       fill=C["muted"], font=F["small"], anchor="center")

    # ══════════════════════════════════════════════════════════════════════════
    # WIDGET HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _make_toggle(self, parent, label, var):
        f = tk.Frame(parent, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
        f.pack(fill="x", padx=2, pady=(0, 4))
        i = tk.Frame(f, bg=C["surface"])
        i.pack(fill="x", padx=8, pady=6)
        dot = tk.Label(i, text="◉", bg=C["surface"],
                        fg=C["green"], font=("Consolas", 10))
        dot.pack(side="left")
        tk.Label(i, text=f"  {label}", bg=C["surface"],
                 fg=C["text"], font=F["small"]).pack(side="left")
        def toggle(e=None):
            var.set(not var.get())
            dot.config(text="◉" if var.get() else "◎",
                        fg=C["green"] if var.get() else C["muted"])
        for w in [f, i, dot]:
            w.bind("<Button-1>", toggle)

    def _set_fmt(self, fmt, btn):
        self._fmt_var.set(fmt)
        for b in self._fmt_btns:
            b.config(bg=C["surface"], fg=C["muted"])
        btn.config(bg=C["cyan_glow"], fg=C["cyan"])

    # ══════════════════════════════════════════════════════════════════════════
    # DRAG & DROP
    # ══════════════════════════════════════════════════════════════════════════

    def _enable_drag_drop(self):
        try:
            from tkinterdnd2 import DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)
        except Exception:
            pass

    def _on_drop(self, e):
        path = e.data.strip().strip("{}")
        if os.path.isfile(path):
            self._load_file(path)

    # ══════════════════════════════════════════════════════════════════════════
    # FILE & BATCH
    # ══════════════════════════════════════════════════════════════════════════

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select Screenshot",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                        ("All files", "*.*")]
        )
        if path:
            self._load_file(path)

    def _browse_batch(self):
        folder = filedialog.askdirectory(title="Select Folder of Images")
        if not folder:
            return
        exts  = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
        files = sorted(
            os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in exts
        )
        if not files:
            messagebox.showinfo("No Images", "No image files found in that folder.")
            return
        self._batch_files = files
        self._batch_idx   = 0
        self._run_batch()

    def _run_batch(self):
        if self._batch_idx >= len(self._batch_files):
            self._batch_lbl.config(
                text=f"✔ Batch complete — {len(self._batch_files)} files",
                fg=C["green"]
            )
            self._refresh_history()
            return
        path = self._batch_files[self._batch_idx]
        self._load_file(path, silent=True)
        self._batch_lbl.config(
            text=f"Batch {self._batch_idx+1}/{len(self._batch_files)}: {os.path.basename(path)}",
            fg=C["yellow"]
        )
        self._extract(batch=True)

    def _load_file(self, path, silent=False):
        self._file = path
        short = os.path.basename(path)
        self._file_lbl.config(text=short, fg=C["text"])
        self._btn_enabled = True
        self._draw_ext_btn(True)
        if not silent:
            self._set_status(f"Loaded: {short}", C["cyan"])
            self._batch_lbl.config(text="")
        self._update_text("")
        self._draw_badge("", C["muted"])
        self._folder_btn.config(text="📂 Outputs", fg=C["text2"])
        self._load_preview(path)

    # ══════════════════════════════════════════════════════════════════════════
    # EXTRACT
    # ══════════════════════════════════════════════════════════════════════════

    def _extract(self, batch=False):
        if not self._file or not self._btn_enabled:
            return
        self._working     = True
        self._is_batch    = batch
        self._btn_enabled = False
        self._draw_ext_btn(False)
        self._draw_status_dot(C["yellow"], "WORKING")
        self._set_status("Processing…", C["yellow"])
        self._draw_badge("working", C["yellow"])
        self._update_text("")

        lang_code = next((c for n, c in LANGS if n == self._lang_var.get()), "eng")
        import core.ocr_engine as om
        om._LANG = lang_code

        self._pipeline.run(
            image_path = self._file,
            auto_open  = self._auto_open_var.get() and self._fmt_var.get() != "clipboard",
            export_fmt = self._fmt_var.get(),
            confidence = self._conf_var.get(),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PIPELINE CALLBACKS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_status(self, msg):
        self.root.after(0, self._set_status, msg, C["yellow"])

    def _on_result(self, result):
        self.root.after(0, self._apply_result, result)

    def _apply_result(self, result):
        self._working = False
        status = result.get("status", "error")

        if status == "success":
            label = result.get("label", "general note")
            text  = result.get("text", "")
            fp    = result.get("filepath") or ""
            color = LABEL_COLORS.get(label, C["text2"])
            self._draw_badge(label, color)
            self._update_text(text)
            fname = os.path.basename(fp) if fp else "clipboard"
            self._folder_btn.config(text=f"📂  {fname}", fg=C["cyan"])
            self._set_status(
                f"✔  {label.upper()} — {len(text):,} chars saved", C["green"])
            self._draw_status_dot(C["green"], "DONE")

        elif status == "empty":
            self._draw_badge("empty", C["yellow"])
            self._update_text(
                "⚠  No text detected.\n\n"
                "Tips:\n"
                "  · Use a higher-resolution screenshot\n"
                "  · Increase UPSCALE_FACTOR in config.py\n"
                "  · Switch to Preview tab → click [ processed ]\n"
                "    to see what Tesseract actually sees"
            )
            self._set_status("No text detected.", C["yellow"])
            self._draw_status_dot(C["yellow"], "EMPTY")

        else:
            msg = result.get("message", "Unknown error")
            self._draw_badge("error", C["red"])
            self._update_text(f"✖  Error:\n\n{msg}")
            self._set_status(f"Error: {msg[:80]}", C["red"])
            self._draw_status_dot(C["red"], "ERROR")

        self._btn_enabled = True
        self._draw_ext_btn(True)
        self._refresh_history()

        if self._is_batch and status == "success":
            self._batch_idx += 1
            self.root.after(500, self._run_batch)
        self._is_batch = False

    # ══════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _copy_text(self):
        txt = self._text_box.get("1.0", "end-1c").strip()
        if txt:
            import pyperclip
            pyperclip.copy(txt)
            self._set_status("✔  Copied to clipboard!", C["green"])

    def _reset(self):
        self._file        = None
        self._batch_files = []
        self._raw_pil     = None
        self._proc_pil    = None
        self._file_lbl.config(text="No file selected", fg=C["muted"])
        self._draw_upload_btn(False)
        self._draw_prev_placeholder()
        self._btn_enabled = False
        self._draw_ext_btn(False)
        self._update_text("")
        self._draw_badge("", C["muted"])
        self._folder_btn.config(text="📂 Outputs", fg=C["text2"])
        self._batch_lbl.config(text="")
        self._set_status("Ready — upload an image to begin.", C["text2"])
        self._draw_status_dot(C["green"], "READY")

    def _open_outputs(self):
        import subprocess
        folder = os.path.abspath("outputs")
        os.makedirs(folder, exist_ok=True)
        try:
            subprocess.Popen(f'explorer "{folder}"')
        except Exception:
            pass

    def _ext_hover(self, on):
        if self._btn_enabled:
            self._draw_ext_btn(True, hover=on)

    # ══════════════════════════════════════════════════════════════════════════
    # HISTORY
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_history(self):
        for w in self._hist_inner.winfo_children():
            w.destroy()
        records = load_all()
        if not records:
            tk.Label(self._hist_inner, text="No extractions yet.",
                      bg=C["surface"], fg=C["muted"],
                      font=F["small"], padx=8, pady=8).pack(anchor="w")
            return
        for rec in records:
            self._history_card(rec)

    def _history_card(self, rec):
        color = LABEL_COLORS.get(rec.get("label", ""), C["muted"])
        fp    = rec.get("filepath", "")
        card  = tk.Frame(self._hist_inner, bg=C["surface2"],
                          highlightbackground=C["border"], highlightthickness=1,
                          cursor="hand2")
        card.pack(fill="x", padx=2, pady=2)
        tk.Frame(card, bg=color, width=3).pack(side="left", fill="y")
        body = tk.Frame(card, bg=C["surface2"])
        body.pack(side="left", fill="x", expand=True, padx=6, pady=4)

        r1 = tk.Frame(body, bg=C["surface2"])
        r1.pack(fill="x")
        tk.Label(r1, text=rec.get("label", "").upper(), bg=C["surface2"],
                  fg=color, font=F["badge"]).pack(side="left")
        tk.Label(r1, text=rec.get("timestamp", "")[-8:], bg=C["surface2"],
                  fg=C["muted"], font=F["micro"]).pack(side="right")

        src = rec.get("source", "")
        src = src if len(src) < 32 else "…" + src[-29:]
        tk.Label(body, text=src, bg=C["surface2"],
                  fg=C["text2"], font=F["micro"], anchor="w").pack(fill="x")

        preview = rec.get("preview", "")
        preview = (preview[:50] + "…") if len(preview) > 50 else preview
        tk.Label(body, text=preview, bg=C["surface2"], fg=C["muted"],
                  font=F["micro"], anchor="w", wraplength=230,
                  justify="left").pack(fill="x")

        r4 = tk.Frame(body, bg=C["surface2"])
        r4.pack(fill="x", pady=(2, 0))
        tk.Label(r4, text=f"{rec.get('chars',0):,} chars", bg=C["surface2"],
                  fg=C["muted"], font=F["micro"]).pack(side="left")
        if fp and fp != "clipboard" and os.path.exists(fp):
            reopen = tk.Label(r4, text="↗ open", bg=C["surface2"],
                               fg=C["cyan"], font=F["micro"], cursor="hand2")
            reopen.pack(side="right")
            reopen.bind("<Button-1>", lambda e, p=fp: self._reopen(p))

        card.bind("<Enter>", lambda e, c=card: c.config(bg=C["border2"]))
        card.bind("<Leave>", lambda e, c=card: c.config(bg=C["surface2"]))

    def _clear_history(self):
        if messagebox.askyesno("Clear History", "Delete all history?"):
            clear_all()
            self._refresh_history()

    def _reopen(self, fp):
        import subprocess
        try:
            subprocess.Popen(["notepad.exe", fp])
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # PREVIEW
    # ══════════════════════════════════════════════════════════════════════════

    def _load_preview(self, path):
        try:
            pil = Image.open(path).convert("RGB")
            self._raw_pil  = pil
            img_cv = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
            gray   = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            proc   = _strategy_dark_code(gray)
            self._proc_pil = Image.fromarray(proc).convert("RGB")
            self._show_proc = False
            self._proc_btn.config(text="[ processed ]", fg=C["muted"])
            self._switch_tab("preview")
            self.root.after(50, self._render_preview)
        except Exception as ex:
            logger.warning(f"Preview error: {ex}")

    def _render_preview(self):
        c = self._prev_c
        c.update_idletasks()
        w = max(c.winfo_width(),  10)
        h = max(c.winfo_height(), 10)
        c.delete("all")
        c.create_rectangle(0, 0, w, h, fill=C["surface"], outline="")
        pil = self._proc_pil if self._show_proc else self._raw_pil
        if not pil:
            c.create_text(w//2, h//2, text="No image loaded",
                           fill=C["muted"], font=F["small"], anchor="center")
            return
        thumb = pil.copy()
        thumb.thumbnail((w - 4, h - 4))
        photo = ImageTk.PhotoImage(thumb)
        self._current_photo = photo          # keep reference!
        c.create_image(w//2, h//2, image=photo, anchor="center")
        lbl = "PROCESSED" if self._show_proc else "ORIGINAL"
        c.create_rectangle(0, 0, w, 16, fill="#00000099", outline="")
        c.create_text(6, 8, text=lbl, fill=C["cyan"],
                       font=F["micro"], anchor="w")

    def _toggle_proc(self):
        self._show_proc = not self._show_proc
        self._proc_btn.config(
            text="[ original ]"  if self._show_proc else "[ processed ]",
            fg=C["cyan"]         if self._show_proc else C["muted"]
        )
        self._render_preview()

    # ══════════════════════════════════════════════════════════════════════════
    # TEXT BOX
    # ══════════════════════════════════════════════════════════════════════════

    def _vsync(self, *args):
        self._text_box.yview(*args)
        self._update_gutter()

    def _update_gutter(self):
        self._gutter.config(state="normal")
        self._gutter.delete("1.0", "end")
        content = self._text_box.get("1.0", "end-1c")
        n = content.count("\n") + 1 if content.strip() else 0
        self._gutter.insert("1.0", "\n".join(str(i+1) for i in range(n)))
        self._gutter.config(state="disabled")

    def _update_text(self, text):
        self._text_box.config(state="normal")
        self._text_box.delete("1.0", "end")
        if text:
            self._text_box.insert("1.0", text)
        self._text_box.config(state="disabled")
        self._update_gutter()

    # ══════════════════════════════════════════════════════════════════════════
    # ANIMATIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _start_animations(self):
        self._anim_scan()
        self._anim_prog()

    def _anim_scan(self):
        self._scan_y = (self._scan_y + 2) % 40
        if self._working:
            c = self._upload_btn
            c.delete("scan")
            c.create_rectangle(0, self._scan_y, 180, self._scan_y + 2,
                                fill=C["cyan_glow"], outline="", tags="scan")
        self.root.after(36, self._anim_scan)

    def _anim_prog(self):
        if self._working:
            self._prog_w = (self._prog_w + 5) % (self._prog_c.winfo_width() or 600)
            c  = self._prog_c
            c.delete("all")
            w  = c.winfo_width() or 600
            c.create_rectangle(0, 0, w, 3, fill=C["surface"], outline="")
            bw = 120
            for i in range(bw):
                ratio = 1.0 - abs(i - bw//2) / (bw//2)
                if ratio > 0.2:
                    px = (self._prog_w - bw//2 + i) % w
                    c.create_rectangle(px, 0, px+2, 3, fill=C["cyan"], outline="")
        else:
            c = self._prog_c
            c.delete("all")
            w = c.winfo_width() or 600
            c.create_rectangle(0, 0, w, 3, fill=C["surface"], outline="")
        self.root.after(18, self._anim_prog)

    # ══════════════════════════════════════════════════════════════════════════
    # RUN
    # ══════════════════════════════════════════════════════════════════════════

    def run(self):
        self.root.mainloop()