"""
config.py — All settings in one place.
"""

# ── OCR ───────────────────────────────────────────────────────────────────────
TESSERACT_CMD  = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
UPSCALE_FACTOR = 2        # raise to 3 for small/blurry text

# ── NLP ───────────────────────────────────────────────────────────────────────
NLP_MODEL                = "cross-encoder/nli-MiniLM2-L6-H768"
CANDIDATE_LABELS         = ["command", "code snippet", "url", "question", "definition", "general note"]
NLP_CONFIDENCE_THRESHOLD = 0.45   # adjustable via UI slider

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_DIR      = "outputs"
EXPORT_FORMATS  = ["txt", "md", "clipboard"]   # shown in export dropdown

# ── History ───────────────────────────────────────────────────────────────────
HISTORY_FILE = "logs/history.json"
MAX_HISTORY  = 50          # max records kept in history

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE  = "logs/app.log"
LOG_LEVEL = "DEBUG"
