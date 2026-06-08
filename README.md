<div align="center">

```

OCR Screen
 
```

### ◈ &nbsp; Q U I C K  &nbsp; S C R E E N  &nbsp; C A P T U R E &nbsp; ◈

> **Screenshot in. Clean text out.**
> *Take a snip → upload → watch the magic.*

# Thanks for [Talha4g](https://github.com/Talha4g) for the idea and [sameer-tech-dev](https://github.com/sameer-tech-dev) for the REPO

---

</div>

<br/>

## ⚡ &nbsp; What Is This?

Please refer to the original [original REPO https://github.com/sameer-tech-dev/Smart-Screen-OCR](https://github.com/sameer-tech-dev/Smart-Screen-OCR) for more information.

## 🎬 &nbsp; The Flow

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   Snipping Tool        ┌─────────────┐                               ║
║   ─────────────►  PNG  │   Your App  │                               ║
║                        └──────┬──────┘                               ║
║                               │                                      ║
║                    ┌──────────▼──────────┐                           ║
║                    │   OpenCV Engine     │  ← 7+1 preprocessing      ║
║                    │   Pre-processing    │    strategies tried       ║
║                    └──────────┬──────────┘                           ║
║                               │                                      ║
║                    ┌──────────▼──────────┐                           ║
║                    │   CNN Classifier    │  ← Zero-shot              ║
║                    │   HuggingFace       │    classification         ║
║                    └──────────┬──────────┘                           ║
║                               │                                      ║
║                    ┌──────────▼──────────┐                           ║
║                    │   LaTeX OCR         │  ← PSM 3, 4, 6 tried      ║
║                    │   Text Extraction   │    best result kept       ║
║                    └──────────┬──────────┘                           ║
║                               │                                      ║
║                               │                                      ║
║                               ▼                                      ║
║                           --------                                   ║
║                     Designated Location                              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

<br/>

---

<br/>

## 🗂️ &nbsp; Project Structure

```

Loading ..

```

<br/>

---

<br/>

## 🛠️ &nbsp; Setup in 4 Steps

Loading ...

<br/>

---

<br/>

## 🎮 &nbsp; Usage

```

Loading .

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

Loading

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

Loading ...

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

Loading ..

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

*"Because time is too much to manually move contexts from screenshots"*

</div>
