"""Launcher script for PyInstaller build."""

import sys
import os

# Add src to path for imports
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    base_path = sys._MEIPASS
else:
    # Running as script
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(base_path, 'src'))

import logging
import customtkinter as ctk

from autobard.config import AppConfig, APP_NAME, APP_VERSION
from autobard.app import AutoBardApp
from autobard.gui.modern_window import ModernWindow


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info(f"{APP_NAME} v{APP_VERSION} starting...")
    
    config = AppConfig.load()
    app = AutoBardApp(config)
    app.start_hotkey_listener()
    
    root = ctk.CTk()
    window = ModernWindow(root, app)
    
    logger.info("Application ready")
    window.run()


if __name__ == "__main__":
    main()
