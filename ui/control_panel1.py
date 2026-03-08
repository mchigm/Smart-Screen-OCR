"""
ui/control_panel.py
Main application window — upload image → extract text → save to Notepad.
Clean dark UI, properly sized, drag-and-drop + file browser support.
"""

from __future__ import annotations
import os
import tkinter as tk
from tkinter import filedialog, ttk
from core.pipeline import Pipeline
from utils.logger import setup_logger

logger = setup_logger()

# ── Palette ───────────────────────────────────────────────────────────────────
C = {
    "bg":         "#0d1117",
    "surface":    "#161b22",
    "surface2":   "#21262d",
    "border":     "#30363d",
    "accent":     "#58a6ff",
    "green":      "#3fb950",
    "yellow":     "#d29922",
    "red":        "#f85149",
    "purple":     "#bc8cff",
    "orange":     "#ffa657",
    "text":       "#e6edf3",
    "muted":      "#8b949e",
    "subtle":     "#484f58",
}

LABEL_COLORS = {
    "code snippet": C["accent"],
    "command":      C["purple"],
    "url":          C["green"],
    "question":     C["orange"],
    "definition":   "#e879f9",
    "general note": C["muted"],
    "empty":        C["subtle"],
    "error":        C["red"],
    "cancelled":    C["subtle"],
}

FONT_TITLE  = ("Consolas", 18, "bold")
FONT_LABEL  = ("Consolas", 10, "bold")
FONT_BODY   = ("Consolas", 10)
FONT_SMALL  = ("Consolas", 9)
FONT_BADGE  = ("Consolas", 9, "bold")


class ControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self._current_file: str | None = None
        self._pipeline = Pipeline(
            on_result=self._on_result,
            on_status=self._on_status,
        )
        self._setup_window()
        self._build_ui()
        self._enable_drag_drop()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.title("Smart Screen OCR")
        self.root.geometry("720x640")
        self.root.minsize(640, 560)
        self.root.configure(bg=C["bg"])
        self.root.resizable(True, True)

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root

        # ── Title bar ─────────────────────────────────────────────────────────
        title_bar = tk.Frame(root, bg=C["bg"])
        title_bar.pack(fill="x", padx=28, pady=(24, 0))

        tk.Label(title_bar, text="◈", bg=C["bg"], fg=C["accent"],
                 font=("Consolas", 20, "bold")).pack(side="left")
        tk.Label(title_bar, text="  Smart Screen OCR", bg=C["bg"], fg=C["text"],
                 font=FONT_TITLE).pack(side="left")

        self._status_dot = tk.Label(title_bar, text="● READY", bg=C["bg"],
                                    fg=C["green"], font=FONT_BADGE)
        self._status_dot.pack(side="right", padx=4)

        tk.Label(root, text="Take a screenshot with Snipping Tool, upload it here — get the text.",
                 bg=C["bg"], fg=C["muted"], font=FONT_SMALL).pack(padx=28, anchor="w", pady=(4, 0))

        self._divider(root)

        # ── Upload zone ───────────────────────────────────────────────────────
        upload_frame = tk.Frame(root, bg=C["surface"], highlightbackground=C["border"],
                                highlightthickness=1)
        upload_frame.pack(fill="x", padx=28, pady=(0, 16))

        inner = tk.Frame(upload_frame, bg=C["surface"])
        inner.pack(pady=28)

        tk.Label(inner, text="⬆", bg=C["surface"], fg=C["accent"],
                 font=("Consolas", 28)).pack()
        tk.Label(inner, text="Drop image here  or", bg=C["surface"],
                 fg=C["muted"], font=FONT_BODY).pack(pady=(6, 10))

        btn_browse = tk.Button(
            inner, text="  Browse File  ",
            command=self._browse,
            bg=C["accent"], fg=C["bg"],
            activebackground="#79b8ff",
            font=("Consolas", 10, "bold"),
            relief="flat", bd=0,
            padx=16, pady=8,
            cursor="hand2"
        )
        btn_browse.pack()

        tk.Label(inner, text="PNG · JPG · BMP · TIFF supported",
                 bg=C["surface"], fg=C["subtle"], font=FONT_SMALL).pack(pady=(10, 0))

        # ── Selected file display ─────────────────────────────────────────────
        file_row = tk.Frame(root, bg=C["bg"])
        file_row.pack(fill="x", padx=28, pady=(0, 6))

        tk.Label(file_row, text="FILE", bg=C["bg"], fg=C["muted"],
                 font=FONT_BADGE).pack(side="left")

        self._file_label = tk.Label(file_row, text="No file selected",
                                    bg=C["bg"], fg=C["subtle"], font=FONT_SMALL)
        self._file_label.pack(side="left", padx=(10, 0))

        # ── Options row ───────────────────────────────────────────────────────
        opts = tk.Frame(root, bg=C["bg"])
        opts.pack(fill="x", padx=28, pady=(0, 12))

        self._auto_open_var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(
            opts,
            text="  Auto-open in Notepad after extraction",
            variable=self._auto_open_var,
            bg=C["bg"], fg=C["text"],
            selectcolor=C["surface2"],
            activebackground=C["bg"],
            activeforeground=C["text"],
            font=FONT_SMALL,
            relief="flat", bd=0,
            cursor="hand2"
        )
        cb.pack(side="left")

        # ── Extract button ────────────────────────────────────────────────────
        self._extract_btn = tk.Button(
            root,
            text="  ▶  Extract Text  ",
            command=self._extract,
            bg=C["green"], fg=C["bg"],
            activebackground="#56d364",
            font=("Consolas", 12, "bold"),
            relief="flat", bd=0,
            padx=24, pady=12,
            cursor="hand2",
            state="disabled"
        )
        self._extract_btn.pack(padx=28, anchor="w")

        self._divider(root)

        # ── Result area ───────────────────────────────────────────────────────
        result_header = tk.Frame(root, bg=C["bg"])
        result_header.pack(fill="x", padx=28, pady=(0, 8))

        tk.Label(result_header, text="RESULT", bg=C["bg"], fg=C["muted"],
                 font=FONT_BADGE).pack(side="left")

        self._badge = tk.Label(result_header, text="", bg=C["surface2"],
                               fg=C["muted"], font=FONT_BADGE, padx=8, pady=2)
        self._badge.pack(side="left", padx=(10, 0))

        self._filepath_label = tk.Label(result_header, text="", bg=C["bg"],
                                        fg=C["accent"], font=FONT_SMALL, cursor="hand2")
        self._filepath_label.pack(side="right")
        self._filepath_label.bind("<Button-1>", self._open_output_folder)

        # Text preview box
        preview_frame = tk.Frame(root, bg=C["border"], padx=1, pady=1)
        preview_frame.pack(fill="both", expand=True, padx=28, pady=(0, 8))

        inner_frame = tk.Frame(preview_frame, bg=C["surface"])
        inner_frame.pack(fill="both", expand=True)

        self._text_box = tk.Text(
            inner_frame,
            bg=C["surface"], fg=C["text"],
            insertbackground=C["text"],
            font=FONT_BODY,
            relief="flat", bd=0,
            wrap="word",
            padx=14, pady=12,
            state="disabled"
        )
        scrollbar = tk.Scrollbar(inner_frame, command=self._text_box.yview,
                                 bg=C["surface2"], troughcolor=C["surface"],
                                 relief="flat", bd=0)
        self._text_box.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._text_box.pack(fill="both", expand=True)

        # ── Status bar ────────────────────────────────────────────────────────
        status_bar = tk.Frame(root, bg=C["surface2"], height=28)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self._status_label = tk.Label(
            status_bar, text="Ready — upload an image to begin.",
            bg=C["surface2"], fg=C["muted"], font=FONT_SMALL
        )
        self._status_label.pack(side="left", padx=16)

        tk.Label(status_bar, text="outputs/ folder  •  logs/app.log",
                 bg=C["surface2"], fg=C["subtle"], font=FONT_SMALL).pack(side="right", padx=16)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _divider(self, parent):
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", padx=28, pady=12)

    def _set_status(self, text: str, color: str = None):
        self._status_label.config(text=text, fg=color or C["muted"])

    def _set_indicator(self, state: str):
        states = {
            "ready":   ("● READY",      C["green"]),
            "working": ("◌ WORKING…",   C["yellow"]),
            "done":    ("✔ DONE",       C["green"]),
            "error":   ("✖ ERROR",      C["red"]),
        }
        text, color = states.get(state, ("● READY", C["green"]))
        self._status_dot.config(text=text, fg=color)

    # ── Drag & Drop ───────────────────────────────────────────────────────────

    def _enable_drag_drop(self):
        """Enable Windows drag-and-drop via tkinterdnd2 if available."""
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            # Re-init root as DnD-capable if tkinterdnd2 is installed
            # Note: for full DnD support install:  pip install tkinterdnd2
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)
            logger.info("Drag-and-drop enabled (tkinterdnd2).")
        except Exception:
            # tkinterdnd2 not installed — silently fall back to browse-only
            logger.info("tkinterdnd2 not found — drag-and-drop disabled. Browse still works.")

    def _on_drop(self, event):
        path = event.data.strip().strip("{}")
        if os.path.isfile(path):
            self._load_file(path)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select Screenshot",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("All files",   "*.*"),
            ]
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        self._current_file = path
        short = os.path.basename(path)
        self._file_label.config(text=f"  {short}", fg=C["text"])
        self._extract_btn.config(state="normal")
        self._set_status(f"File loaded: {short}")
        # Clear previous result
        self._update_text_box("")
        self._badge.config(text="", fg=C["muted"])
        self._filepath_label.config(text="")
        logger.info(f"File selected: {path}")

    def _extract(self):
        if not self._current_file:
            return
        self._extract_btn.config(state="disabled")
        self._set_indicator("working")
        self._set_status("Processing…", C["yellow"])
        self._update_text_box("")
        self._badge.config(text="  WORKING…  ", fg=C["yellow"])

        self._pipeline.run(
            image_path=self._current_file,
            auto_open_notepad=self._auto_open_var.get()
        )

    # ── Pipeline Callbacks ────────────────────────────────────────────────────

    def _on_status(self, msg: str):
        """Called from background thread — schedule on main thread."""
        self.root.after(0, self._set_status, msg)

    def _on_result(self, result: dict):
        self.root.after(0, self._apply_result, result)

    def _apply_result(self, result: dict):
        status = result.get("status", "error")

        if status == "success":
            label    = result.get("label", "general note")
            text     = result.get("text", "")
            filepath = result.get("filepath", "")
            score    = result.get("score", 0)

            color = LABEL_COLORS.get(label, C["muted"])
            badge_text = f"  {label.upper()}  {score:.0%}  "

            self._badge.config(text=badge_text, fg=color, bg=C["surface2"])
            self._update_text_box(text)
            self._filepath_label.config(
                text=f"📂 {os.path.basename(filepath)}",
                fg=C["accent"]
            )
            self._filepath_label._filepath = filepath
            self._set_status(f"Saved → {filepath}", C["green"])
            self._set_indicator("done")

        elif status == "empty":
            self._badge.config(text="  NO TEXT  ", fg=C["yellow"], bg=C["surface2"])
            self._update_text_box("⚠  No text was detected in this image.\n\nTips:\n• Make sure the image contains readable text\n• Try a higher-resolution screenshot\n• Avoid very stylised or handwritten fonts")
            self._set_status("No text detected.", C["yellow"])
            self._set_indicator("error")

        elif status == "error":
            msg = result.get("message", "Unknown error")
            self._badge.config(text="  ERROR  ", fg=C["red"], bg=C["surface2"])
            self._update_text_box(f"✖  Error:\n\n{msg}")
            self._set_status(f"Error: {msg}", C["red"])
            self._set_indicator("error")

        self._extract_btn.config(state="normal")

    def _update_text_box(self, text: str):
        self._text_box.config(state="normal")
        self._text_box.delete("1.0", "end")
        if text:
            self._text_box.insert("1.0", text)
        self._text_box.config(state="disabled")

    def _open_output_folder(self, event=None):
        import subprocess
        folder = os.path.abspath("outputs")
        os.makedirs(folder, exist_ok=True)
        try:
            subprocess.Popen(f'explorer "{folder}"')
        except Exception:
            pass

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()
