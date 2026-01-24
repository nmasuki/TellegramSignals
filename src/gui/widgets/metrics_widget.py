"""System metrics widget"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont


class MetricsWidget(QWidget):
    """Widget displaying system metrics"""

    view_error_log_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Metrics group
        metrics_group = QGroupBox("System Metrics")
        metrics_layout = QVBoxLayout(metrics_group)

        # Messages
        self.messages_label = QLabel("Messages: 0")
        metrics_layout.addWidget(self.messages_label)

        # Extracted
        self.extracted_label = QLabel("Extracted: 0")
        metrics_layout.addWidget(self.extracted_label)

        # Errors
        self.errors_label = QLabel("Errors: 0")
        self.errors_label.setStyleSheet("color: red;")
        metrics_layout.addWidget(self.errors_label)

        # Success rate
        self.success_rate_label = QLabel("Success: --")
        font = QFont()
        font.setBold(True)
        self.success_rate_label.setFont(font)
        metrics_layout.addWidget(self.success_rate_label)

        metrics_layout.addSpacing(10)

        # Last error
        self.last_error_label = QLabel("Last Error:\n  --")
        self.last_error_label.setStyleSheet("color: gray; font-size: 10px;")
        self.last_error_label.setWordWrap(True)
        metrics_layout.addWidget(self.last_error_label)

        # View error log button
        view_errors_btn = QPushButton("View Error Log")
        view_errors_btn.clicked.connect(self.view_error_log_requested.emit)
        metrics_layout.addWidget(view_errors_btn)

        layout.addWidget(metrics_group)

        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        # Start/Stop button
        self.start_stop_btn = QPushButton("Start Monitoring")
        self.start_stop_btn.setCheckable(True)
        actions_layout.addWidget(self.start_stop_btn)

        # Settings button
        self.settings_btn = QPushButton("Settings")
        actions_layout.addWidget(self.settings_btn)

        # Open CSV button
        self.open_csv_btn = QPushButton("Open CSV File")
        actions_layout.addWidget(self.open_csv_btn)

        layout.addWidget(actions_group)

    def update_message_count(self, count: int):
        """Update message count"""
        self.messages_label.setText(f"Messages: {count:,}")

    def update_extracted_count(self, count: int):
        """Update extracted signal count"""
        self.extracted_label.setText(f"Extracted: {count:,}")

    def update_error_count(self, count: int):
        """Update error count"""
        self.errors_label.setText(f"Errors: {count:,}")

    def update_success_rate(self, rate: float):
        """Update success rate"""
        if rate >= 0:
            color = "green" if rate >= 90 else "orange" if rate >= 70 else "red"
            self.success_rate_label.setText(f"Success: {rate:.1f}%")
            self.success_rate_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        else:
            self.success_rate_label.setText("Success: --")

    def update_last_error(self, error_text: str, time_ago: str):
        """Update last error information"""
        self.last_error_label.setText(f"Last Error:\n  {time_ago}\n  {error_text[:50]}...")

    def set_monitoring_state(self, is_monitoring: bool):
        """Update start/stop button state"""
        self.start_stop_btn.setChecked(is_monitoring)
        self.start_stop_btn.setText("Stop Monitoring" if is_monitoring else "Start Monitoring")

    def refresh(self):
        """Refresh metrics"""
        pass
