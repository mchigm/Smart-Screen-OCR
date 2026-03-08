"""
core/pipeline.py
Orchestrates: image path → OCR → NLP → save → history.
Runs OCR+NLP in a background thread; UI stays responsive.
"""

from __future__ import annotations
import threading
from core.ocr_engine    import image_to_text
from core.nlp_classifier import classify
from core.text_saver    import save
from core.history_manager import add_record
from utils.logger       import setup_logger

logger = setup_logger()


class Pipeline:
    def __init__(self, on_result=None, on_status=None):
        self.on_result  = on_result   # callback(result_dict)
        self.on_status  = on_status   # callback(status_str)
        self._running   = False

    def run(self, image_path: str, auto_open: bool = True,
            export_fmt: str = "txt", confidence: float | None = None):
        """Non-blocking — spawns daemon thread."""
        if self._running:
            logger.warning("Already processing — please wait.")
            return
        threading.Thread(
            target=self._run,
            args=(image_path, auto_open, export_fmt, confidence),
            daemon=True
        ).start()

    def _run(self, image_path: str, auto_open: bool,
             export_fmt: str, confidence: float | None):
        self._running = True
        try:
            # Step 1 — OCR
            self._status("Extracting text from image…")
            text = image_to_text(image_path)
            if not text:
                self._finish({"status": "empty", "message": "No text found.", "filepath": None})
                return

            # Step 2 — Classify (with optional live confidence override)
            self._status("Classifying content…")
            result = classify(text, confidence_override=confidence)

            # Step 3 — Save / export
            self._status(f"Saving as .{export_fmt}…" if export_fmt != "clipboard"
                         else "Copying to clipboard…")
            filepath = save(
                text=result["clean_text"],
                label=result["label"],
                source_filename=image_path,
                fmt=export_fmt,
                auto_open=auto_open
            )

            # Step 4 — Write history
            add_record(
                source=image_path,
                label=result["label"],
                score=result["score"],
                text=result["clean_text"],
                filepath=filepath or "clipboard",
            )

            self._finish({
                "status":   "success",
                "label":    result["label"],
                "score":    result["score"],
                "text":     result["clean_text"],
                "filepath": filepath,
                "fmt":      export_fmt,
                "message":  f"Done — {result['label'].upper()}",
            })

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            self._finish({"status": "error", "message": str(e), "filepath": None})
        finally:
            self._running = False

    def _status(self, msg: str):
        logger.info(msg)
        if self.on_status:
            self.on_status(msg)

    def _finish(self, result: dict):
        logger.info(f"Pipeline → {result.get('message','done')}")
        if self.on_result:
            self.on_result(result)
