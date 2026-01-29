"""Add Channel Dialog"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QDoubleSpinBox
)
from PySide6.QtCore import Qt


class AddChannelDialog(QDialog):
    """Dialog for adding/editing a Telegram channel"""

    def __init__(self, parent=None, edit_mode=False, channel_data=None):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.channel_data = channel_data or {}
        self.setWindowTitle("Edit Channel" if edit_mode else "Add Channel")
        self.setMinimumWidth(400)
        self.channel_username = None
        self.channel_description = None
        self.channel_confidence = 1.0
        self.setup_ui()

    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Enter the Telegram channel username (without @).\n"
            "The channel must be public or you must be a member."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(instructions)

        # Username input
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("@"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("channel_username")
        self.username_input.textChanged.connect(self.validate_input)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # Description input
        layout.addWidget(QLabel("Description (optional):"))
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Brief description of this channel")
        layout.addWidget(self.description_input)

        # Confidence input
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("Channel Confidence:"))
        self.confidence_input = QDoubleSpinBox()
        self.confidence_input.setRange(0.0, 1.0)
        self.confidence_input.setSingleStep(0.05)
        self.confidence_input.setDecimals(2)
        self.confidence_input.setValue(1.0)
        self.confidence_input.setToolTip(
            "Multiplier applied to signal confidence (0.0-1.0).\n"
            "Based on channel reliability/win rate research.\n"
            "1.0 = full trust, 0.5 = 50% confidence reduction"
        )
        confidence_layout.addWidget(self.confidence_input)
        confidence_layout.addStretch()
        layout.addLayout(confidence_layout)

        # Pre-fill values in edit mode
        if self.edit_mode and self.channel_data:
            self.username_input.setText(self.channel_data.get('username', ''))
            self.username_input.setEnabled(False)  # Can't change username
            self.description_input.setText(self.channel_data.get('description', ''))
            self.confidence_input.setValue(self.channel_data.get('confidence', 1.0))

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.add_btn = QPushButton("Save" if self.edit_mode else "Add Channel")
        self.add_btn.setEnabled(self.edit_mode)  # Enable immediately in edit mode
        self.add_btn.clicked.connect(self.accept_channel)
        self.add_btn.setDefault(True)
        button_layout.addWidget(self.add_btn)

        layout.addLayout(button_layout)

    def validate_input(self):
        """Validate username input"""
        username = self.username_input.text().strip()
        # Remove @ if user typed it
        if username.startswith('@'):
            username = username[1:]
            self.username_input.setText(username)

        # Enable button only if username is valid
        is_valid = len(username) >= 3 and username.replace('_', '').isalnum()
        self.add_btn.setEnabled(is_valid)

    def accept_channel(self):
        """Accept and store channel data"""
        username = self.username_input.text().strip()
        if username.startswith('@'):
            username = username[1:]

        self.channel_username = username
        self.channel_description = self.description_input.text().strip() or f"{username} signals"
        self.channel_confidence = self.confidence_input.value()
        self.accept()

    def get_channel_data(self):
        """Return channel data"""
        data = {
            'username': self.channel_username,
            'description': self.channel_description,
            'confidence': self.channel_confidence,
            'enabled': self.channel_data.get('enabled', True) if self.edit_mode else True
        }
        return data
