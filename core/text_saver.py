"""
core/text_saver.py
Saves extracted text in the chosen format: txt / md / clipboard.
Optionally opens the file in Notepad.
"""

from __future__ import annotations
import os
import subprocess
import datetime
import pyperclip
from config import OUTPUT_DIR
from utils.logger import setup_logger

logger = setup_logger()


def save(text: str, label: str, source_filename: str,
         fmt: str = "txt", auto_open: bool = True) -> str | None:
    """
    Save extracted text in the requested format.

    fmt options:
      "txt"       — plain .txt file (default)
      "md"        — Markdown .md file with heading + code fence for code
      "clipboard" — copy to clipboard only, no file saved

    Returns saved filepath, or None for clipboard-only.
    """
    if fmt == "clipboard":
        pyperclip.copy(text)
        logger.info("Copied to clipboard (no file saved).")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base      = os.path.splitext(os.path.basename(source_filename))[0]
    ext       = "md" if fmt == "md" else "txt"
    filename  = f"{timestamp}_{base}_{label.replace(' ', '_')}.{ext}"
    filepath  = os.path.join(OUTPUT_DIR, filename)

    content = _build_md(text, label, source_filename) if fmt == "md" \
              else _build_txt(text, label, source_filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Saved [{fmt}]: {filepath}")

    if auto_open:
        _open(filepath)

    return filepath


# ── Format builders ───────────────────────────────────────────────────────────

def _build_txt(text: str, label: str, source: str) -> str:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"========================================\n"
        f"  Smart Screen OCR — Extracted Text\n"
        f"========================================\n"
        f"  Source  : {os.path.basename(source)}\n"
        f"  Type    : {label.upper()}\n"
        f"  Saved at: {now}\n"
        f"========================================\n\n"
        f"{text}\n"
    )


def _build_md(text: str, label: str, source: str) -> str:
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icon = {"code snippet": "💻", "command": "⌨️", "url": "🔗",
            "question": "❓", "definition": "📖"}.get(label, "📝")

    # Wrap code/command in fenced block
    if label in ("code snippet", "command"):
        lang = "bash" if label == "command" else ""
        body = f"```{lang}\n{text}\n```"
    else:
        body = text

    return (
        f"# {icon} Extracted Text — {label.upper()}\n\n"
        f"> **Source:** `{os.path.basename(source)}`  \n"
        f"> **Saved:** {now}\n\n"
        f"---\n\n"
        f"{body}\n"
    )


# ── Open helper ───────────────────────────────────────────────────────────────

def _open(filepath: str):
    try:
        subprocess.Popen(["notepad.exe", filepath])
        logger.info("Opened in Notepad.")
    except FileNotFoundError:
        try:
            subprocess.Popen(["xdg-open", filepath])
        except Exception:
            logger.warning("Could not auto-open. Find file in outputs/")
