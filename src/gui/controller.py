"""Application controller - coordinates GUI and backend"""
import logging
from PySide6.QtCore import QObject, QTimer

from src.gui.worker import BackgroundWorker
from src.gui.settings_dialog import SettingsDialog
from src.gui.add_channel_dialog import AddChannelDialog
from src.gui.error_log_dialog import ErrorLogDialog


class AppController(QObject):
    """Controller that coordinates GUI components with backend"""

    def __init__(self, main_window, config):
        super().__init__()
        self.main_window = main_window
        self.config = config
        self.worker = None
        self.logger = logging.getLogger(__name__)

        # Settings dialog
        self.settings_dialog = None

        # Setup
        self.setup_connections()
        self.initialize_ui()

        # Start monitoring automatically
        self.start_monitoring()

    def setup_connections(self):
        """Connect signals between components"""
        # Main window signals
        self.main_window.settings_requested.connect(self.show_settings)
        self.main_window.exit_requested.connect(self.exit_application)

        # Tray icon signals
        self.main_window.tray_icon.exit_requested.connect(self.exit_application)
        self.main_window.tray_icon.monitoring_toggled.connect(self.toggle_monitoring)

        # Widget signals
        self.main_window.metrics_widget.start_stop_btn.clicked.connect(self.toggle_monitoring_from_button)
        self.main_window.metrics_widget.settings_btn.clicked.connect(self.show_settings)
        self.main_window.metrics_widget.open_csv_btn.clicked.connect(self.on_open_csv_file)

        # Channel widget signals
        self.main_window.channel_widget.add_channel_requested.connect(self.on_add_channel_requested)
        self.main_window.channel_widget.edit_channel_requested.connect(self.on_edit_channel_requested)

        # Metrics widget signals
        self.main_window.metrics_widget.view_error_log_requested.connect(self.on_view_error_log)

    def initialize_ui(self):
        """Initialize UI with current config"""
        # Add configured channels to channel widget
        channels = self.config.get_enabled_channels()
        for channel in channels:
            username = channel.get('username')
            enabled = channel.get('enabled', True)
            confidence = channel.get('confidence', 1.0)
            if username:
                self.main_window.channel_widget.add_channel(username, enabled, confidence)

        # Set CSV path in status bar
        csv_path = self.config.get_csv_path()
        self.main_window.csv_path_label.setText(f"CSV: {csv_path}")

        # Add initial log messages
        self.main_window.add_activity_log("Application initialized", "info")

    def start_monitoring(self):
        """Start background monitoring"""
        if self.worker and self.worker.isRunning():
            self.logger.warning("Worker already running")
            return

        self.logger.info("Starting background worker")
        self.main_window.add_activity_log("Starting monitoring...", "info")

        # Create worker
        self.worker = BackgroundWorker(self.config)

        # Connect worker signals
        self.worker.status_changed.connect(self.on_status_changed)
        self.worker.signal_extracted.connect(self.on_signal_extracted)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.message_received.connect(self.on_message_received)
        self.worker.stats_updated.connect(self.on_stats_updated)
        self.worker.log_message.connect(self.on_log_message)
        self.worker.request_auth_code.connect(self.on_request_auth_code)
        self.worker.request_2fa_password.connect(self.on_request_2fa_password)

        # Start worker
        self.worker.start()

        # Update UI
        self.main_window.update_status("connecting", "orange")
        self.main_window.metrics_widget.set_monitoring_state(True)
        self.main_window.tray_icon.update_monitoring_state(True)

    def stop_monitoring(self):
        """Stop background monitoring"""
        if not self.worker or not self.worker.isRunning():
            self.logger.warning("Worker not running")
            return

        self.logger.info("Stopping background worker")
        self.main_window.add_activity_log("Stopping monitoring...", "info")

        # Stop worker
        self.worker.stop()
        self.worker.wait(5000)  # Wait up to 5 seconds

        # Update UI
        self.main_window.update_status("stopped", "gray")
        self.main_window.metrics_widget.set_monitoring_state(False)
        self.main_window.tray_icon.update_monitoring_state(False)

    def toggle_monitoring(self, start: bool):
        """Toggle monitoring on/off"""
        if start:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def toggle_monitoring_from_button(self):
        """Toggle monitoring from button click"""
        is_monitoring = self.main_window.metrics_widget.start_stop_btn.isChecked()
        self.toggle_monitoring(is_monitoring)

    # Worker signal handlers
    def on_status_changed(self, status: str):
        """Handle status change from worker"""
        self.main_window.update_status(status)
        self.logger.info(f"Status changed: {status}")

    def on_signal_extracted(self, signal_data: dict):
        """Handle signal extracted from worker"""
        # Add to signal table
        self.main_window.add_signal_to_table(signal_data)

        # Update channel signal count
        channel = signal_data.get('channel_username')
        if channel:
            self.main_window.channel_widget.increment_channel_signal_count(channel)

        # Show notification
        symbol = signal_data.get('symbol', '')
        direction = signal_data.get('direction', '')
        entry = signal_data.get('entry_price') or signal_data.get('entry_price_min', '')
        confidence = signal_data.get('confidence_score', 0)
        conf_pct = confidence * 100 if confidence else 0

        notification_title = f"New Signal from @{channel}, {conf_pct:.0f}% confidence"
        notification_text = f"{symbol} {direction} @ {entry}"
        self.main_window.tray_icon.show_notification(
            notification_title,
            notification_text,
            3000
        )

    def on_error_occurred(self, error_message: str, level: str):
        """Handle error from worker"""
        self.logger.error(f"Worker error: {error_message}")

        # Add to activity log
        self.main_window.add_activity_log(error_message, level)

        # Show warning status if too many errors
        # (implement error rate monitoring if needed)

    def on_message_received(self, channel: str, preview: str):
        """Handle message received from worker"""
        # Update channel last activity
        from datetime import datetime
        self.main_window.channel_widget.update_channel_activity(
            channel,
            "just now"
        )

    def on_stats_updated(self, stats: dict):
        """Handle stats update from worker"""
        # Update metrics widget
        self.main_window.metrics_widget.update_message_count(stats['messages'])
        self.main_window.metrics_widget.update_extracted_count(stats['extracted'])
        self.main_window.metrics_widget.update_error_count(stats['errors'])

        success_rate = stats.get('success_rate', -1)
        self.main_window.metrics_widget.update_success_rate(success_rate)

        # Update signal count
        self.main_window.update_signal_count(stats['extracted'])

        # Update uptime
        uptime = stats.get('uptime', '00:00:00')
        self.main_window.update_uptime(uptime)

    def on_log_message(self, message: str, level: str):
        """Handle log message from worker"""
        self.main_window.add_activity_log(message, level)

    def on_request_auth_code(self):
        """Handle request for Telegram auth code"""
        from PySide6.QtWidgets import QInputDialog

        self.logger.info("Requesting Telegram verification code from user")
        self.main_window.add_activity_log("Please enter Telegram verification code", "info")

        # Show input dialog for verification code
        code, ok = QInputDialog.getText(
            self.main_window,
            "Telegram Verification",
            "Enter the verification code sent to your Telegram app or phone:",
            )

        if ok and code:
            self.logger.info("User provided verification code")
            self.worker.provide_auth_code(code)
        else:
            self.logger.warning("User cancelled verification code input")
            self.worker.provide_auth_code("")  # Provide empty to unblock

    def on_request_2fa_password(self):
        """Handle request for Telegram 2FA password"""
        from PySide6.QtWidgets import QInputDialog, QLineEdit

        self.logger.info("Requesting Telegram 2FA password from user")
        self.main_window.add_activity_log("Please enter your 2FA password", "info")

        # Show input dialog for 2FA password (hidden input)
        password, ok = QInputDialog.getText(
            self.main_window,
            "Telegram 2FA",
            "Your account has Two-Factor Authentication enabled.\nEnter your 2FA password:",
            QLineEdit.Password
        )

        if ok and password:
            self.logger.info("User provided 2FA password")
            self.worker.provide_2fa_password(password)
        else:
            self.logger.warning("User cancelled 2FA password input")
            self.worker.provide_2fa_password("")  # Provide empty to unblock

    def on_add_channel_requested(self):
        """Handle add channel request"""
        dialog = AddChannelDialog(self.main_window)
        if dialog.exec():
            channel_data = dialog.get_channel_data()
            username = channel_data.get('username', '')
            description = channel_data.get('description', '')
            confidence = channel_data.get('confidence', 1.0)

            if username:
                # Add to config
                self.config.add_channel(username, description, confidence=confidence)

                # Add to UI
                self.main_window.channel_widget.add_channel(username, enabled=True, confidence=confidence)

                # Log
                display_name = description if description else username
                self.main_window.add_activity_log(f"Added channel: @{username} ({display_name})", "info")
                self.logger.info(f"Added channel: @{username}")

                # If monitoring is active, need to restart to pick up new channel
                if self.worker and self.worker.isRunning():
                    from PySide6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self.main_window,
                        "Restart Monitoring",
                        "Restart monitoring to pick up the new channel?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if reply == QMessageBox.Yes:
                        self.stop_monitoring()
                        self.start_monitoring()

    def on_edit_channel_requested(self, username: str):
        """Handle edit channel request"""
        # Get current channel data from config
        channels = self.config.get_channels()
        channel_data = next((ch for ch in channels if ch.get('username') == username), None)

        if not channel_data:
            self.logger.warning(f"Channel {username} not found in config")
            return

        dialog = AddChannelDialog(self.main_window, edit_mode=True, channel_data=channel_data)
        if dialog.exec():
            new_data = dialog.get_channel_data()
            description = new_data.get('description', '')
            confidence = new_data.get('confidence', 1.0)

            # Update config
            self.config.update_channel(username, description=description, confidence=confidence)

            # Update UI
            self.main_window.channel_widget.update_channel_confidence(username, confidence)

            # Log
            self.main_window.add_activity_log(
                f"Updated @{username}: confidence={int(confidence*100)}%", "info"
            )
            self.logger.info(f"Updated channel: @{username} (confidence={confidence})")

    def on_open_csv_file(self):
        """Open CSV file from config path"""
        import os
        import subprocess
        import sys

        csv_path = self.config.get_csv_path()
        if csv_path.exists():
            if sys.platform == 'win32':
                os.startfile(str(csv_path))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(csv_path)])
            else:
                subprocess.run(['xdg-open', str(csv_path)])
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.main_window,
                "File Not Found",
                f"CSV file not found:\n{csv_path}"
            )

    def on_view_error_log(self):
        """Handle view error log request"""
        error_log_path = self.config.get_error_log_path()
        dialog = ErrorLogDialog(error_log_path, self.main_window)
        dialog.exec()

    def show_settings(self):
        """Show settings dialog"""
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self.config, self.main_window)

        self.settings_dialog.exec()

        # Reload config if settings were saved
        # (Settings dialog handles saving)

    def exit_application(self):
        """Exit the application"""
        self.logger.info("Exiting application")

        # Stop monitoring
        if self.worker and self.worker.isRunning():
            self.stop_monitoring()

        # Hide tray icon
        self.main_window.tray_icon.hide()

        # Set force close flag and close main window
        self.main_window.force_close = True
        self.main_window.close()

        # Quit application
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
