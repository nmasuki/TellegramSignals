"""Channel list widget"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class ChannelWidget(QWidget):
    """Widget displaying monitored channels"""

    channel_selected = Signal(str)  # Emits channel username
    add_channel_requested = Signal()
    edit_channel_requested = Signal(str)  # Emits channel username for editing

    def __init__(self):
        super().__init__()
        self.channels = {}
        self.setup_ui()

    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Group box
        group = QGroupBox("Monitored Channels")
        group_layout = QVBoxLayout(group)

        # Channel list
        self.channel_list = QListWidget()
        self.channel_list.itemClicked.connect(self.on_channel_clicked)
        self.channel_list.itemDoubleClicked.connect(self.on_channel_double_clicked)
        group_layout.addWidget(self.channel_list)

        # Add channel button
        add_button = QPushButton("+ Add Channel")
        add_button.clicked.connect(self.add_channel_requested.emit)
        group_layout.addWidget(add_button)

        layout.addWidget(group)

    def add_channel(self, username: str, enabled: bool = True, confidence: float = 1.0):
        """Add channel to list"""
        # Create list item
        item = QListWidgetItem()

        # Create widget for item
        widget = QWidget()
        widget_layout = QVBoxLayout(widget)
        widget_layout.setContentsMargins(5, 5, 5, 5)

        # Status indicator + name
        header_layout = QVBoxLayout()

        status_text = f"● {username}" if enabled else f"○ {username}"
        name_label = QLabel(status_text)
        font = QFont()
        font.setBold(True)
        name_label.setFont(font)
        header_layout.addWidget(name_label)

        # Confidence indicator
        confidence_pct = int(confidence * 100)
        confidence_label = QLabel(f"Confidence: {confidence_pct}%")
        if confidence >= 0.7:
            confidence_label.setStyleSheet("color: #4CAF50; font-size: 10px;")  # Green
        elif confidence >= 0.5:
            confidence_label.setStyleSheet("color: #FF9800; font-size: 10px;")  # Orange
        else:
            confidence_label.setStyleSheet("color: #f44336; font-size: 10px;")  # Red
        header_layout.addWidget(confidence_label)

        # Last activity
        last_activity_label = QLabel("Last: --")
        last_activity_label.setStyleSheet("color: gray; font-size: 10px;")
        header_layout.addWidget(last_activity_label)

        # Signal count
        signal_count_label = QLabel("Signals: 0")
        signal_count_label.setStyleSheet("color: gray; font-size: 10px;")
        header_layout.addWidget(signal_count_label)

        widget_layout.addLayout(header_layout)

        # Store channel data
        self.channels[username] = {
            'enabled': enabled,
            'confidence': confidence,
            'item': item,
            'widget': widget,
            'name_label': name_label,
            'confidence_label': confidence_label,
            'last_activity_label': last_activity_label,
            'signal_count_label': signal_count_label,
            'signal_count': 0
        }

        # Add to list
        item.setSizeHint(widget.sizeHint())
        self.channel_list.addItem(item)
        self.channel_list.setItemWidget(item, widget)

    def update_channel_activity(self, username: str, last_activity: str):
        """Update channel last activity time"""
        if username in self.channels:
            self.channels[username]['last_activity_label'].setText(f"Last: {last_activity}")

    def update_channel_signal_count(self, username: str, count: int):
        """Update channel signal count"""
        if username in self.channels:
            self.channels[username]['signal_count'] = count
            self.channels[username]['signal_count_label'].setText(f"Signals: {count}")

    def increment_channel_signal_count(self, username: str):
        """Increment signal count for channel"""
        if username in self.channels:
            count = self.channels[username]['signal_count'] + 1
            self.update_channel_signal_count(username, count)

    def set_channel_enabled(self, username: str, enabled: bool):
        """Set channel enabled state"""
        if username in self.channels:
            self.channels[username]['enabled'] = enabled
            status_text = f"● {username}" if enabled else f"○ {username}"
            self.channels[username]['name_label'].setText(status_text)

    def clear_channels(self):
        """Clear all channels"""
        self.channel_list.clear()
        self.channels.clear()

    def refresh(self):
        """Refresh channel display"""
        # Refresh logic if needed
        pass

    def on_channel_clicked(self, item):
        """Handle channel click"""
        # Find username for this item
        for username, data in self.channels.items():
            if data['item'] == item:
                self.channel_selected.emit(username)
                break

    def on_channel_double_clicked(self, item):
        """Handle channel double-click to edit"""
        for username, data in self.channels.items():
            if data['item'] == item:
                self.edit_channel_requested.emit(username)
                break

    def update_channel_confidence(self, username: str, confidence: float):
        """Update channel confidence display"""
        if username in self.channels:
            self.channels[username]['confidence'] = confidence
            confidence_pct = int(confidence * 100)
            label = self.channels[username]['confidence_label']
            label.setText(f"Confidence: {confidence_pct}%")
            if confidence >= 0.7:
                label.setStyleSheet("color: #4CAF50; font-size: 10px;")
            elif confidence >= 0.5:
                label.setStyleSheet("color: #FF9800; font-size: 10px;")
            else:
                label.setStyleSheet("color: #f44336; font-size: 10px;")

    def get_channel_data(self, username: str) -> dict:
        """Get channel data for editing"""
        if username in self.channels:
            return {
                'username': username,
                'enabled': self.channels[username]['enabled'],
                'confidence': self.channels[username].get('confidence', 1.0)
            }
        return None
