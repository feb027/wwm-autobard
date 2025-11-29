"""Entry point for running autobard as a module: python -m autobard"""

import logging
import customtkinter as ctk

from .config import AppConfig, APP_NAME, APP_VERSION
from .app import AutoBardApp
from .gui.modern_window import ModernWindow


def main() -> None:
    """Main entry point for WWM Auto-Bard."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    logger.info(f"{APP_NAME} v{APP_VERSION} starting...")
    
    config = AppConfig.load()
    app = AutoBardApp(config)
    app.start_hotkey_listener()
    
    # Use CustomTkinter for modern UI
    root = ctk.CTk()
    window = ModernWindow(root, app)
    
    logger.info("Application ready")
    window.run()


if __name__ == "__main__":
    main()
