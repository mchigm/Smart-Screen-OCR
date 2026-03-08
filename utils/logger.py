"""utils/logger.py — Shared logger."""

import logging
import os
from config import LOG_FILE, LOG_LEVEL

_done = False

def setup_logger(name: str = "smart_ocr") -> logging.Logger:
    global _done
    logger = logging.getLogger(name)
    if not _done:
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)
        fmt = logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s", datefmt="%H:%M:%S")
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        _done = True
    return logger
