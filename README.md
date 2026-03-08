<div align="center">

```
 ██████╗  ██████╗██████╗    ███████╗ ██████╗██████╗ ███████╗███████╗███╗   ██╗
██╔═══██╗██╔════╝██╔══██╗   ██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝████╗  ██║
██║   ██║██║     ██████╔╝   ███████╗██║     ██████╔╝█████╗  █████╗  ██╔██╗ ██║
██║   ██║██║     ██╔══██╗   ╚════██║██║     ██╔══██╗██╔══╝  ██╔══╝  ██║╚██╗██║
╚██████╔╝╚██████╗██║  ██║   ███████║╚██████╗██║  ██║███████╗███████╗██║ ╚████║
 ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝
```

### ◈ &nbsp; C O N T E X T U A L &nbsp; M E E T I N G &nbsp; A S S I S T A N T &nbsp; ◈

<br/>

[![Python](https://img.shields.io/badge/Python-3.10.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![Tesseract](https://img.shields.io/badge/Tesseract-OCR-FF6F00?style=for-the-badge&logo=google&logoColor=white)](https://github.com/UB-Mannheim/tesseract)
[![HuggingFace](https://img.shields.io/badge/🤗_HuggingFace-Transformers-FFD21E?style=for-the-badge)](https://huggingface.co)
[![Tkinter](https://img.shields.io/badge/Tkinter-GUI-1976D2?style=for-the-badge&logo=python&logoColor=white)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

> **Screenshot in. Clean text out.**
> *Take a snip → upload → watch the magic.*

<br/>

---

</div>

<br/>

## ⚡ &nbsp; What Is This?

You're in a meeting. There's a **code snippet on a slide**. A **terminal error in a video**. A **command in a tutorial screenshot**. You can't copy it — it's an image.

**Smart Screen OCR fixes that.**

```
  📸  Take screenshot          →    🧠  OCR extracts text
  ⬆   Upload to app            →    🏷  NLP detects type
  ✨  Get clean .txt file       →    📂  Opens in Notepad
```

Under **5 seconds**. Zero manual typing. Works on dark terminals, code editors, slides — anything.

<br/>

---

<br/>

## 🎬 &nbsp; The Flow

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   Win+Shift+S          ┌─────────────┐                              ║
║   ─────────────►  PNG  │   Your App  │                              ║
║   Snipping Tool        └──────┬──────┘                              ║
║                               │                                      ║
║                    ┌──────────▼──────────┐                          ║
║                    │   OpenCV Engine     │  ← 5 preprocessing       ║
║                    │   Pre-processing    │    strategies tried       ║
║                    └──────────┬──────────┘                          ║
║                               │                                      ║
║                    ┌──────────▼──────────┐                          ║
║                    │   Tesseract OCR     │  ← PSM 3, 4, 6 tried     ║
║                    │   Text Extraction   │    best result kept       ║
║                    └──────────┬──────────┘                          ║
║                               │                                      ║
║                    ┌──────────▼──────────┐                          ║
║                    │   NLP Classifier    │  ← Zero-shot             ║
║                    │   HuggingFace       │    classification         ║
║                    └──────────┬──────────┘                          ║
║                               │                                      ║
║              ┌────────────────┼────────────────┐                    ║
║              ▼                ▼                ▼                    ║
║         code snippet        url            question                 ║
║         ──────────          ─────          ────────                 ║
║         saved to        browser opens    Google search             ║
║         outputs/          instantly        URL opened              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

<br/>

---

<br/>

## 🗂️ &nbsp; Project Structure

```
smart-screen-ocr/
│
├── 🚀  main.py                ← Entry point — python main.py
├── ⚙️  config.py              ← ALL settings in one place
├── 📦  requirements.txt       ← pip install -r requirements.txt
│
├── 🧠  core/
│   ├── ocr_engine.py          ← Image → Text  (OpenCV + Tesseract)
│   ├── nlp_classifier.py      ← Text → Label  (HuggingFace NLP)
│   ├── text_saver.py          ← Label + Text → .txt + Notepad
│   └── pipeline.py            ← Orchestrates all 3 steps
│
├── 🖥️  ui/
│   └── control_panel.py       ← Tkinter dark-theme GUI
│
├── 🔧  utils/
│   └── logger.py              ← Console + file logging
│
├── 📂  outputs/               ← Your extracted .txt files land here
└── 📋  logs/
    └── app.log                ← Auto-created on first run
```

<br/>

---

<br/>

## 🛠️ &nbsp; Setup in 4 Steps

### Step 1 &nbsp;—&nbsp; Install Tesseract Binary

| OS | Command |
|:---|:--------|
| 🪟 **Windows** | [Download installer](https://github.com/UB-Mannheim/tesseract/wiki) → install to default path |
| 🍎 **macOS** | `brew install tesseract` |
| 🐧 **Linux** | `sudo apt install tesseract-ocr` |

<br/>

### Step 2 &nbsp;—&nbsp; Create Virtual Environment

```bash
cd smart-screen-ocr
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

<br/>

### Step 3 &nbsp;—&nbsp; Install Dependencies (ORDER MATTERS)

```bash
# 1. Pin NumPy first — prevents version conflicts with OpenCV
pip install "numpy==1.26.4"

# 2. PyTorch CPU (lighter, no GPU needed)
pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# 3. Everything else
pip install -r requirements.txt
```

<br/>

### Step 4 &nbsp;—&nbsp; Verify & Run

```bash
# Quick sanity check
python -c "import cv2; print('cv2 ✓', cv2.__version__)"
python -c "import pytesseract; print('tesseract ✓')"

# Launch
python main.py
```

<br/>

---

<br/>

## 🎮 &nbsp; Usage

```
1.  Press  Win + Shift + S   →  draw a box around any text on screen

2.  Save the screenshot anywhere on your PC

3.  In the app:
    ┌─────────────────────────────────┐
    │  ⬆  Drop image here  or        │
    │     [ Browse File ]             │
    └─────────────────────────────────┘

4.  Click  ▶ Extract Text

5.  Watch the magic:
    ✦  Text extracted by OCR
    ✦  Type detected by NLP
    ✦  File saved to outputs/
    ✦  Notepad opens automatically
```

<br/>

---

<br/>

## 🏷️ &nbsp; Smart Label Detection

The NLP engine automatically classifies what it reads into 6 types:

| Badge | Label | What It Means |
|:------|:------|:--------------|
| 🔵 | **code snippet** | Source code block |
| 🟣 | **command** | Terminal / shell command |
| 🟢 | **url** | Web link — fast detected, no model needed |
| 🟠 | **question** | A question worth searching |
| 🩷 | **definition** | Explanation or definition |
| ⚫ | **general note** | Anything else |

Output files are named automatically:

```
outputs/
  20250610_143022_screenshot_code_snippet.txt
  20250610_151100_error_log_command.txt
  20250610_160045_slide_general_note.txt
```

<br/>

---

<br/>

## 🧪 &nbsp; OCR Strategy Engine

The secret behind accurate extraction — **5 strategies race each other**. The winner is whichever extracts the most text:

```
Image Input
    │
    ├──► 🌑  dark_code       Invert → Denoise → Sharpen → 3x Upscale → Binary
    │                        ↑ PRIMARY — built for VS Code, terminals, dark slides
    │
    ├──► 🔄  inverted_otsu   Inverts + Otsu auto-threshold
    │
    ├──► ☀️  otsu             Standard Otsu — light backgrounds
    │
    ├──► 🌊  adaptive         Per-region threshold — uneven backgrounds
    │
    └──► 🔲  plain_upscale   Raw upscale only — already clean images
              │
              └──  Best result → Tesseract PSM 6 / 4 / 3 all tried → longest wins
```

<br/>

---

<br/>

## ⚙️ &nbsp; Configuration

All settings live in **`config.py`** — one file, no hunting through code:

```python
# ── Path to Tesseract ──────────────────────────────────────────────
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ── Image quality boost before OCR ────────────────────────────────
# Increase to 3 for small or blurry text
UPSCALE_FACTOR = 2

# ── NLP Model ──────────────────────────────────────────────────────
# Downloads once (~120 MB), cached forever after
NLP_MODEL = "cross-encoder/nli-MiniLM2-L6-H768"

# ── Classification labels ──────────────────────────────────────────
CANDIDATE_LABELS = ["command", "code snippet", "url",
                    "question", "definition", "general note"]

# ── Confidence gate ────────────────────────────────────────────────
# Below this score → falls back to "general note"
NLP_CONFIDENCE_THRESHOLD = 0.45

# ── Output folder ──────────────────────────────────────────────────
OUTPUT_DIR = "outputs"
```

<br/>

---

<br/>

## 🩺 &nbsp; Troubleshooting

| Problem | Fix |
|:--------|:----|
| `TesseractNotFoundError` | Set full `.exe` path in `TESSERACT_CMD` inside `config.py` |
| `numpy / cv2 import error` | `pip install "numpy==1.26.4"` then `pip install opencv-python==4.8.1.78 --force-reinstall` |
| NLP model not found | Set `NLP_MODEL = "cross-encoder/nli-MiniLM2-L6-H768"` in `config.py` |
| OCR text still garbled | Set `UPSCALE_FACTOR = 3` in `config.py` |
| No text detected | Screenshot too low-res or stylised font — try a higher-res snip |
| `KeyboardInterrupt` on close | Normal — just means you closed the window ✓ |
| Slow on first extraction | NLP model downloading once (~120 MB). All runs after are fast. |

<br/>

---

<br/>

## 📦 &nbsp; Dependencies

```
opencv-python   ==  4.8.1.78    Image processing & preprocessing
Pillow          ==  10.3.0      Image loading fallback
pytesseract     ==  0.3.10      Tesseract OCR Python wrapper
transformers    ==  4.35.2      HuggingFace NLP pipelines
torch           ==  2.2.2       Model inference (CPU only)
numpy           ==  1.26.4      Array operations (must be < 2.0)
pyperclip       ==  1.8.2       Clipboard support
```

> 💡 **Optional:** `pip install tkinterdnd2` to enable drag-and-drop image support

<br/>

---

<br/>

## 🗺️ &nbsp; Roadmap

```
  ✅  Dark terminal / code OCR
  ✅  Multi-strategy preprocessing  (5 strategies)
  ✅  NLP zero-shot classification  (6 labels)
  ✅  Auto-save timestamped .txt files
  ✅  Auto-open in Notepad
  ✅  Dark-theme Tkinter UI  (720×640)

  🔲  Drag-and-drop image support   (tkinterdnd2)
  🔲  Batch processing              (multiple images at once)
  🔲  Copy to Clipboard button
  🔲  Multi-language OCR            (Hindi, French, Arabic...)
  🔲  System tray icon              (pystray)
  🔲  Fully offline LLM             (Ollama integration)
  🔲  Extraction history panel      (last 10 results)
```

<br/>

---

<br/>

## 📁 &nbsp; Output File Format

Every extracted file includes a clean, readable header:

```
========================================
  Smart Screen OCR — Extracted Text
========================================
  Source  : terminal_error.png
  Type    : COMMAND
  Saved at: 2025-06-10 14:32:10
========================================

pip install "numpy==1.26.4"
pip install opencv-python==4.8.1.78 --force-reinstall
```

<br/>

---

<br/>

<div align="center">

```
  Built with  ♥  using Python · OpenCV · Tesseract · HuggingFace · Tkinter
```

**MIT License** &nbsp;·&nbsp; Free to use, modify, and share

<br/>

*"Because life is too short to manually type code from screenshots."*

</div>
