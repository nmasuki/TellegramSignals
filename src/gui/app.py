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

    # Load configuration (without validation to handle missing config gracefully)
    try:
        config = ConfigManager(validate=False)

        # Check if configuration is valid
        is_valid, error_msg = config.is_valid()
        if not is_valid:
            # Show error dialog with instructions
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Configuration Required")
            msg.setText("Telegram Signal Extractor requires configuration before first use.")

            # Determine config path for user
            config_dir = config.project_root / "config"
            env_file = config_dir / ".env"
            config_file = config.config_path

            msg.setInformativeText(
                f"Configuration error: {error_msg}\n\n"
                f"Configuration location: {config_dir}\n\n"
                "Setup steps:\n\n"
                f"1. Create a '.env' file at:\n   {env_file}\n\n"
                "2. Add your Telegram API credentials:\n"
                "   TELEGRAM_API_ID=your_api_id\n"
                "   TELEGRAM_API_HASH=your_api_hash\n"
                "   TELEGRAM_PHONE=+1234567890\n\n"
                "3. Get API credentials from:\n   https://my.telegram.org\n\n"
                f"4. (Optional) Edit {config_file.name}\n   to add channels to monitor."
            )
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            sys.exit(1)

    except Exception as e:
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Configuration Error")
        msg.setText("Failed to load configuration.")
        msg.setInformativeText(str(e))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        sys.exit(1)

    # Set up logging (pass project_root for correct path resolution)
    logging_config = config.config.get('logging', {})
    setup_logging(logging_config, config.project_root)

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
