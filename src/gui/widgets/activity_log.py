"""Activity log widget"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout
)
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat
from PySide6.QtCore import Qt
from datetime import datetime


class ActivityLogWidget(QWidget):
    """Widget displaying activity log"""

    def __init__(self):
        super().__init__()
        self.max_entries = 100
        self.entry_count = 0
        self.setup_ui()

    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Activity Log")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Text edit for log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)

        # Style
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, Monaco, monospace;
                font-size: 10px;
                border: 1px solid #3e3e3e;
            }
        """)

        layout.addWidget(self.log_text)

    def add_message(self, message: str, level: str = "info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color code by level
        color_map = {
            "info": "#58a6ff",      # Blue
            "success": "#3fb950",   # Green
            "warning": "#d29922",   # Orange
            "error": "#f85149",     # Red
            "debug": "#8b949e"      # Gray
        }

        color = color_map.get(level, "#d4d4d4")

        # Create formatted message
        formatted_message = f'<span style="color: #8b949e;">{timestamp}</span> <span style="color: {color};">{message}</span><br>'

        # Add to log
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertHtml(formatted_message)
        self.log_text.moveCursor(QTextCursor.End)

        # Increment counter
        self.entry_count += 1

        # Trim if too many entries
        if self.entry_count > self.max_entries:
            # Remove first line
            cursor = self.log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove newline
            self.entry_count -= 1

    def add_info(self, message: str):
        """Add info message"""
        self.add_message(message, "info")

    def add_success(self, message: str):
        """Add success message"""
        self.add_message(message, "success")

    def add_warning(self, message: str):
        """Add warning message"""
        self.add_message(message, "warning")

    def add_error(self, message: str):
        """Add error message"""
        self.add_message(message, "error")

    def add_debug(self, message: str):
        """Add debug message"""
        self.add_message(message, "debug")

    def clear(self):
        """Clear all log entries"""
        self.log_text.clear()
        self.entry_count = 0
