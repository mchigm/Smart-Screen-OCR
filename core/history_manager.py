"""
core/history_manager.py
Reads and writes extraction history to logs/history.json.
Each record stores: timestamp, source filename, label, char count, filepath.
Max MAX_HISTORY records — oldest dropped automatically.
"""

from __future__ import annotations
import os
import json
import datetime
from config import HISTORY_FILE, MAX_HISTORY
from utils.logger import setup_logger

logger = setup_logger()


def add_record(source: str, label: str, score: float, text: str, filepath: str):
    """Append one extraction record. Trims to MAX_HISTORY."""
    records = load_all()
    records.insert(0, {
        "timestamp":  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source":     os.path.basename(source),
        "label":      label,
        "score":      round(score, 3),
        "chars":      len(text),
        "filepath":   filepath,
        "preview":    text[:120].replace("\n", " "),
    })
    records = records[:MAX_HISTORY]
    _save(records)
    logger.debug(f"History: added record for {os.path.basename(source)}")


def load_all() -> list[dict]:
    """Return all history records (newest first). Empty list if none."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"History read error: {e}")
        return []


def clear_all():
    """Wipe the history file."""
    _save([])
    logger.info("History cleared.")


def _save(records: list[dict]):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"History write error: {e}")
