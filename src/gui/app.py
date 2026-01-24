"""Desktop GUI application entry point"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.gui.main_window import MainWindow
from src.gui.controller import AppController
from src.config.config_manager import ConfigManager
from src.utils.logging_setup import setup_logging


def main():
    """Main GUI application entry point"""
    # Set up application
    app = QApplication(sys.argv)
    app.setApplicationName("Telegram Signal Extractor")
    app.setOrganizationName("TelegramSignals")
    app.setQuitOnLastWindowClosed(False)  # Continue running when window closed

    # Set application icon
    app_icon = get_app_icon()
    if app_icon:
        app.setWindowIcon(app_icon)

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Load configuration
    config = ConfigManager()

    # Set up logging
    logging_config = config.config.get('logging', {})
    setup_logging(logging_config)

    # Create main window and controller
    main_window = MainWindow()
    controller = AppController(main_window, config)

    # Show main window
    main_window.show()

    # Start application event loop
    sys.exit(app.exec())


def get_app_icon():
    """Get application icon"""
    # Try to load icon from resources
    icon_path = Path(__file__).parent / "resources" / "icons" / "app.png"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return None


if __name__ == "__main__":
    main()
