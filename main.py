"""
main.py — Entry point.
Run:  python main.py
"""

from ui.control_panel import ControlPanel
from utils.logger import setup_logger

logger = setup_logger()

if __name__ == "__main__":
    logger.info("Starting Smart Screen OCR...")
    app = ControlPanel()
    app.run()
    logger.info("Application closed.")
