"""
core/nlp_classifier.py
Zero-shot classification — returns label + confidence.
Accepts optional confidence_override so the UI slider works live.
"""

from __future__ import annotations
import re
from transformers import pipeline
from config import NLP_MODEL, CANDIDATE_LABELS, NLP_CONFIDENCE_THRESHOLD
from utils.logger import setup_logger

logger = setup_logger()
_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        logger.info(f"Loading NLP model: {NLP_MODEL}")
        _classifier = pipeline("zero-shot-classification", model=NLP_MODEL)
        logger.info("NLP model ready.")
    return _classifier


def classify(text: str, confidence_override: float | None = None) -> dict:
    """
    Returns { "label": str, "score": float, "clean_text": str }
    confidence_override: if set, replaces NLP_CONFIDENCE_THRESHOLD for this call.
    """
    threshold = confidence_override if confidence_override is not None \
                else NLP_CONFIDENCE_THRESHOLD

    if not text or len(text.strip()) < 3:
        return {"label": "empty", "score": 0.0, "clean_text": text}

    if re.search(r"https?://\S+", text):
        return {"label": "url", "score": 1.0, "clean_text": text.strip()}

    try:
        clf    = _get_classifier()
        result = clf(text, candidate_labels=CANDIDATE_LABELS)
        label  = result["labels"][0]
        score  = result["scores"][0]

        if score < threshold:
            label = "general note"

        clean = _clean_code(text) if label in ("code snippet", "command") \
                else text.strip()

        logger.info(f"Classified [{label}] {score:.0%}")
        return {"label": label, "score": score, "clean_text": clean}

    except Exception as e:
        logger.error(f"NLP error: {e}")
        return {"label": "general note", "score": 0.0, "clean_text": text.strip()}


def _clean_code(text: str) -> str:
    lines   = text.splitlines()
    cleaned = [re.sub(r"^\s*\d+\s*[|:]?\s*", "", l) for l in lines]
    return "\n".join(cleaned).strip()
