"""Error Log Viewer Dialog"""
import json
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ErrorLogDialog(QDialog):
    """Dialog for viewing extraction errors"""

    def __init__(self, error_log_path: str, parent=None):
        super().__init__(parent)
        self.error_log_path = Path(error_log_path)
        self.errors = []
        self.setWindowTitle("Extraction Error Log")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.load_errors()

    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout(self)

        # Header with stats
        header_layout = QHBoxLayout()
        self.stats_label = QLabel("Loading...")
        header_layout.addWidget(self.stats_label)
        header_layout.addStretch()

        # Filter dropdown
        header_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Errors", "Last 24 Hours", "Last 7 Days"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        header_layout.addWidget(self.filter_combo)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_errors)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Splitter for table and details
        splitter = QSplitter(Qt.Vertical)

        # Error table
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(5)
        self.error_table.setHorizontalHeaderLabels([
            "Time", "Channel", "Error Reason", "Confidence", "Fields Found"
        ])
        self.error_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.error_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.error_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.error_table.itemSelectionChanged.connect(self.on_selection_changed)
        splitter.addWidget(self.error_table)

        # Details panel
        details_group = QGroupBox("Error Details")
        details_layout = QVBoxLayout(details_group)

        # Raw message
        details_layout.addWidget(QLabel("Raw Message:"))
        self.raw_message_text = QTextEdit()
        self.raw_message_text.setReadOnly(True)
        self.raw_message_text.setMaximumHeight(100)
        self.raw_message_text.setFont(QFont("Consolas", 10))
        details_layout.addWidget(self.raw_message_text)

        # Extracted fields
        details_layout.addWidget(QLabel("Extracted Fields:"))
        self.fields_text = QTextEdit()
        self.fields_text.setReadOnly(True)
        self.fields_text.setMaximumHeight(100)
        self.fields_text.setFont(QFont("Consolas", 10))
        details_layout.addWidget(self.fields_text)

        splitter.addWidget(details_group)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        open_file_btn = QPushButton("Open Log File")
        open_file_btn.clicked.connect(self.open_log_file)
        button_layout.addWidget(open_file_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def load_errors(self):
        """Load errors from log file"""
        self.errors = []

        if not self.error_log_path.exists():
            self.stats_label.setText("No error log file found")
            self.error_table.setRowCount(0)
            return

        try:
            with open(self.error_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            error = json.loads(line)
                            self.errors.append(error)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            self.stats_label.setText(f"Error loading log: {e}")
            return

        self.stats_label.setText(f"Total Errors: {len(self.errors)}")
        self.apply_filter()

    def apply_filter(self):
        """Apply time filter to errors"""
        filter_text = self.filter_combo.currentText()
        filtered = self.errors.copy()

        if filter_text == "Last 24 Hours":
            cutoff = datetime.now().timestamp() - (24 * 60 * 60)
            filtered = [e for e in filtered if self._get_timestamp(e) > cutoff]
        elif filter_text == "Last 7 Days":
            cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)
            filtered = [e for e in filtered if self._get_timestamp(e) > cutoff]

        self.populate_table(filtered)

    def _get_timestamp(self, error: dict) -> float:
        """Get timestamp from error entry"""
        ts = error.get('timestamp', '')
        if isinstance(ts, str) and ts:
            try:
                # Handle ISO format
                if 'T' in ts:
                    ts = ts.replace('T', ' ')[:19]
                return datetime.fromisoformat(ts).timestamp()
            except:
                pass
        return 0

    def populate_table(self, errors: list):
        """Populate table with errors"""
        self.error_table.setRowCount(len(errors))

        for row, error in enumerate(reversed(errors)):  # Most recent first
            # Time
            timestamp = error.get('timestamp', 'Unknown')
            if isinstance(timestamp, str) and len(timestamp) > 19:
                timestamp = timestamp[:19].replace('T', ' ')
            self.error_table.setItem(row, 0, QTableWidgetItem(str(timestamp)))

            # Channel
            channel = error.get('channel_username', 'Unknown')
            self.error_table.setItem(row, 1, QTableWidgetItem(channel))

            # Error reason
            reason = error.get('error_reason', 'Unknown')
            self.error_table.setItem(row, 2, QTableWidgetItem(reason))

            # Confidence (if available in extracted fields)
            fields = error.get('extracted_fields', {})
            confidence = fields.get('confidence', '--')
            self.error_table.setItem(row, 3, QTableWidgetItem(str(confidence)))

            # Fields found count
            found = sum(1 for v in fields.values() if v is not None and v != '' and v != [])
            self.error_table.setItem(row, 4, QTableWidgetItem(f"{found} fields"))

            # Store full error data
            self.error_table.item(row, 0).setData(Qt.UserRole, error)

    def on_selection_changed(self):
        """Handle table selection change"""
        selected = self.error_table.selectedItems()
        if not selected:
            return

        # Get error data from first column
        row = selected[0].row()
        error = self.error_table.item(row, 0).data(Qt.UserRole)

        if error:
            # Show raw message
            raw_msg = error.get('raw_message', 'N/A')
            self.raw_message_text.setText(raw_msg)

            # Show extracted fields
            fields = error.get('extracted_fields', {})
            fields_str = json.dumps(fields, indent=2, default=str)
            self.fields_text.setText(fields_str)

    def clear_log(self):
        """Clear the error log file"""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Clear Error Log",
            "Are you sure you want to clear the error log?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Truncate the file
                with open(self.error_log_path, 'w', encoding='utf-8') as f:
                    pass
                self.load_errors()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear log: {e}")

    def open_log_file(self):
        """Open log file in default application"""
        import os
        import subprocess
        import sys

        if self.error_log_path.exists():
            if sys.platform == 'win32':
                os.startfile(str(self.error_log_path))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(self.error_log_path)])
            else:
                subprocess.run(['xdg-open', str(self.error_log_path)])
