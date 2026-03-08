"""
core/ocr_engine.py
Optimised for dark-background code/terminal screenshots.
Pipeline: invert → denoise → sharpen → upscale → OCR
Also tries other strategies as fallback.
"""

from __future__ import annotations
import cv2
import numpy as np
import pytesseract
from PIL import Image
from config import TESSERACT_CMD, UPSCALE_FACTOR
from utils.logger import setup_logger

logger = setup_logger()
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

_LANG = "eng"   # overridden at runtime by UI language selector


def image_to_text(image_path: str) -> str:
    img  = _load(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    strategies = {
        "dark_code":     _strategy_dark_code(gray),      # PRIMARY — dark bg, light text
        "inverted_otsu": _strategy_inverted_otsu(gray),  # fallback dark
        "otsu":          _strategy_otsu(gray),            # light bg fallback
        "adaptive":      _strategy_adaptive(gray),        # uneven bg fallback
        "plain_upscale": _upscale(gray),                  # no processing fallback
    }

    best_label, best_text = "", ""
    for label, processed in strategies.items():
        text = _run_ocr(processed)
        logger.debug(f"[{label:16s}] {len(text):4d} chars | preview: {text[:60].strip()!r}")
        if len(text) > len(best_text):
            best_text  = text
            best_label = label

    logger.info(f"Winner: [{best_label}] — {len(best_text)} chars")
    return best_text.strip()


# ── Strategies ────────────────────────────────────────────────────────────────

def _strategy_dark_code(gray: np.ndarray) -> np.ndarray:
    """
    Specifically tuned for VS Code / terminal / dark-theme screenshots.
    Steps:
      1. Invert so text becomes dark-on-white (Tesseract works best this way)
      2. Denoise to remove colour bleed from syntax highlighting
      3. Sharpen edges so character shapes are crisp
      4. Upscale with cubic interpolation
      5. Otsu threshold for clean binary image
    """
    # Step 1 — invert (light text → dark text)
    inverted = cv2.bitwise_not(gray)

    # Step 2 — denoise
    denoised = cv2.fastNlMeansDenoising(inverted, h=12, templateWindowSize=7, searchWindowSize=21)

    # Step 3 — sharpen
    kernel = np.array([[0, -1,  0],
                       [-1, 5, -1],
                       [0, -1,  0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)

    # Step 4 — upscale
    h, w = sharpened.shape
    factor = max(UPSCALE_FACTOR, 3)   # at least 3x for code text
    upscaled = cv2.resize(sharpened, (w * factor, h * factor),
                          interpolation=cv2.INTER_CUBIC)

    # Step 5 — clean binary threshold
    _, binary = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def _strategy_inverted_otsu(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    upscaled = _upscale(blur)
    _, thresh = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return thresh


def _strategy_otsu(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    upscaled = _upscale(blur)
    _, thresh = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def _strategy_adaptive(gray: np.ndarray) -> np.ndarray:
    upscaled = _upscale(gray)
    blur = cv2.GaussianBlur(upscaled, (3, 3), 0)
    return cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11, C=2
    )


def _upscale(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape
    factor = max(UPSCALE_FACTOR, 2)
    return cv2.resize(gray, (w * factor, h * factor), interpolation=cv2.INTER_CUBIC)


# ── Loaders ───────────────────────────────────────────────────────────────────

def _load(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        pil = Image.open(path).convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    logger.debug(f"Loaded: {path}  shape={img.shape}")
    return img


# ── OCR runner ────────────────────────────────────────────────────────────────

def _run_ocr(img: np.ndarray) -> str:
    """
    PSM modes:
      6 = single uniform block of text     ← best for code blocks
      4 = single column, variable sizes    ← good for terminal output
      3 = fully automatic                  ← general fallback
    """
    best = ""
    for psm in [6, 4, 3]:
        try:
            # OEM 3 = LSTM neural net (most accurate)
            config = f"--psm {psm} --oem 3 -l {_LANG}"
            text = pytesseract.image_to_string(img, config=config).strip()
            if len(text) > len(best):
                best = text
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract not found.\n"
                "Install: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "Set TESSERACT_CMD in config.py"
            )
        except Exception:
            continue
    return best
