"""Settings dialog"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox,
    QGroupBox, QMessageBox, QDoubleSpinBox, QFileDialog
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    """Multi-tab settings dialog"""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()

        # Add tabs
        self.tabs.addTab(self.create_telegram_tab(), "Telegram")
        self.tabs.addTab(self.create_channels_tab(), "Channels")
        self.tabs.addTab(self.create_extraction_tab(), "Extraction")
        self.tabs.addTab(self.create_output_tab(), "Output")
        self.tabs.addTab(self.create_gui_tab(), "GUI")

        layout.addWidget(self.tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_settings)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def create_telegram_tab(self):
        """Create Telegram configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # API credentials group
        group = QGroupBox("Telegram API Credentials")
        group_layout = QVBoxLayout(group)

        # API ID
        api_id_layout = QHBoxLayout()
        api_id_layout.addWidget(QLabel("API ID:"))
        self.api_id_input = QLineEdit()
        api_id_layout.addWidget(self.api_id_input)
        group_layout.addLayout(api_id_layout)

        # API Hash
        api_hash_layout = QHBoxLayout()
        api_hash_layout.addWidget(QLabel("API Hash:"))
        self.api_hash_input = QLineEdit()
        self.api_hash_input.setEchoMode(QLineEdit.Password)
        api_hash_layout.addWidget(self.api_hash_input)
        group_layout.addLayout(api_hash_layout)

        # Phone
        phone_layout = QHBoxLayout()
        phone_layout.addWidget(QLabel("Phone:"))
        self.phone_input = QLineEdit()
        phone_layout.addWidget(self.phone_input)
        group_layout.addLayout(phone_layout)

        layout.addWidget(group)

        # Session group
        session_group = QGroupBox("Session")
        session_layout = QVBoxLayout(session_group)

        self.session_status_label = QLabel("Status: Connected")
        session_layout.addWidget(self.session_status_label)

        reconnect_btn = QPushButton("Reconnect")
        session_layout.addWidget(reconnect_btn)

        clear_session_btn = QPushButton("Clear Session")
        session_layout.addWidget(clear_session_btn)

        layout.addWidget(session_group)

        layout.addStretch()

        return widget

    def create_channels_tab(self):
        """Create channel management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Channel Management")
        group_layout = QVBoxLayout(group)

        info_label = QLabel(
            "Channel configuration is managed in config/config.yaml.\n"
            "Edit the file and restart the application to apply changes."
        )
        info_label.setWordWrap(True)
        group_layout.addWidget(info_label)

        open_config_btn = QPushButton("Open Configuration File")
        open_config_btn.clicked.connect(self.open_config_file)
        group_layout.addWidget(open_config_btn)

        layout.addWidget(group)
        layout.addStretch()

        return widget

    def create_extraction_tab(self):
        """Create extraction settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Extraction Settings")
        group_layout = QVBoxLayout(group)

        # Min confidence
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("Minimum Confidence:"))
        self.min_confidence_spin = QDoubleSpinBox()
        self.min_confidence_spin.setRange(0.0, 1.0)
        self.min_confidence_spin.setSingleStep(0.05)
        self.min_confidence_spin.setDecimals(2)
        confidence_layout.addWidget(self.min_confidence_spin)
        confidence_layout.addStretch()
        group_layout.addLayout(confidence_layout)

        info_label = QLabel("Signals below this threshold will be logged as errors.")
        info_label.setStyleSheet("color: gray; font-size: 10px;")
        group_layout.addWidget(info_label)

        layout.addWidget(group)
        layout.addStretch()

        return widget

    def create_output_tab(self):
        """Create output configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Output Configuration")
        group_layout = QVBoxLayout(group)

        # CSV file
        csv_layout = QHBoxLayout()
        csv_layout.addWidget(QLabel("CSV File:"))
        self.csv_path_input = QLineEdit()
        csv_layout.addWidget(self.csv_path_input)
        browse_csv_btn = QPushButton("Browse")
        browse_csv_btn.clicked.connect(lambda: self.browse_file(self.csv_path_input, "CSV"))
        csv_layout.addWidget(browse_csv_btn)
        group_layout.addLayout(csv_layout)

        # Error log
        error_layout = QHBoxLayout()
        error_layout.addWidget(QLabel("Error Log:"))
        self.error_log_input = QLineEdit()
        error_layout.addWidget(self.error_log_input)
        browse_error_btn = QPushButton("Browse")
        browse_error_btn.clicked.connect(lambda: self.browse_file(self.error_log_input, "JSONL"))
        error_layout.addWidget(browse_error_btn)
        group_layout.addLayout(error_layout)

        # System log
        system_log_layout = QHBoxLayout()
        system_log_layout.addWidget(QLabel("System Log:"))
        self.system_log_input = QLineEdit()
        system_log_layout.addWidget(self.system_log_input)
        browse_system_btn = QPushButton("Browse")
        browse_system_btn.clicked.connect(lambda: self.browse_file(self.system_log_input, "LOG"))
        system_log_layout.addWidget(browse_system_btn)
        group_layout.addLayout(system_log_layout)

        layout.addWidget(group)
        layout.addStretch()

        return widget

    def create_gui_tab(self):
        """Create GUI preferences tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Notifications group
        notif_group = QGroupBox("Notifications")
        notif_layout = QVBoxLayout(notif_group)

        self.enable_notifications_check = QCheckBox("Enable desktop notifications")
        notif_layout.addWidget(self.enable_notifications_check)

        self.notif_signals_check = QCheckBox("Notify on new signals")
        notif_layout.addWidget(self.notif_signals_check)

        self.notif_errors_check = QCheckBox("Notify on errors and warnings")
        notif_layout.addWidget(self.notif_errors_check)

        layout.addWidget(notif_group)

        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)

        self.minimize_to_tray_check = QCheckBox("Minimize to tray on close")
        behavior_layout.addWidget(self.minimize_to_tray_check)

        self.start_minimized_check = QCheckBox("Start minimized")
        behavior_layout.addWidget(self.start_minimized_check)

        layout.addWidget(behavior_group)

        layout.addStretch()

        return widget

    def load_settings(self):
        """Load current settings"""
        # Telegram
        telegram_config = self.config.get_telegram_config()
        self.api_id_input.setText(str(telegram_config.get('api_id', '')))
        self.api_hash_input.setText(telegram_config.get('api_hash', ''))
        self.phone_input.setText(telegram_config.get('phone', ''))

        # Extraction
        min_confidence = self.config.get_min_confidence()
        self.min_confidence_spin.setValue(min_confidence)

        # Output
        csv_path = self.config.get_csv_path()
        self.csv_path_input.setText(str(csv_path))

        error_log_path = self.config.get_error_log_path()
        self.error_log_input.setText(str(error_log_path))

        # GUI preferences (defaults for now)
        self.enable_notifications_check.setChecked(True)
        self.notif_signals_check.setChecked(True)
        self.notif_errors_check.setChecked(True)
        self.minimize_to_tray_check.setChecked(True)
        self.start_minimized_check.setChecked(False)

    def apply_settings(self):
        """Apply settings"""
        # For now, just show a message
        # Full implementation would update config and restart components
        QMessageBox.information(
            self,
            "Settings",
            "Settings will be applied on next restart.\n"
            "To change settings now, edit the .env and config.yaml files."
        )

    def accept_settings(self):
        """Accept and close"""
        self.apply_settings()
        self.accept()

    def browse_file(self, line_edit, file_type):
        """Browse for file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Select {file_type} File",
            line_edit.text(),
            f"{file_type} Files (*.{file_type.lower()})"
        )

        if file_path:
            line_edit.setText(file_path)

    def open_config_file(self):
        """Open config file"""
        import subprocess
        import os
        from pathlib import Path

        config_path = Path("config/config.yaml")
        if config_path.exists():
            if os.name == 'nt':  # Windows
                os.startfile(str(config_path))
            else:
                subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', str(config_path)))
