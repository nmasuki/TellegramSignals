"""Signal table widget"""
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from datetime import datetime


def _clean(value, default=None):
    """Return None for NaN/empty values, otherwise the value itself."""
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    if isinstance(value, str) and value.strip().lower() in ('nan', ''):
        return default
    return value


def _fmt(value, fallback='--'):
    """Format a value for display: return fallback for None/NaN."""
    v = _clean(value)
    if v is None:
        return fallback
    return str(v)


class SignalTableWidget(QWidget):
    """Widget displaying recent signals in a table"""

    signal_selected = Signal(dict)  # Emits signal data
    view_all_requested = Signal()
    export_requested = Signal()

    def __init__(self):
        super().__init__()
        self.signals = []
        self.max_signals = 100  # Keep last 100 signals
        self.setup_ui()

    def setup_ui(self):
        """Set up UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header with label and buttons
        header_layout = QHBoxLayout()

        title_label = QLabel("Recent Signals")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Buttons
        view_all_btn = QPushButton("View All")
        view_all_btn.clicked.connect(self.view_all_requested.emit)
        header_layout.addWidget(view_all_btn)

        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_requested.emit)
        header_layout.addWidget(export_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_table)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "Time", "MsgID", "Channel", "Symbol", "Direction", "Entry",
            "SL", "TP1", "TP2", "TP3", "TP4", "Conf", "Status"
        ])

        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)   # Time
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)   # MsgID
        header.setSectionResizeMode(2, QHeaderView.Stretch)            # Channel
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)   # Symbol
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)   # Direction
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)   # Entry
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)   # SL
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)   # TP1
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)   # TP2
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)   # TP3
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)  # TP4
        header.setSectionResizeMode(11, QHeaderView.ResizeToContents)  # Conf
        header.setSectionResizeMode(12, QHeaderView.ResizeToContents)  # Status

        # Double-click to view details
        self.table.doubleClicked.connect(self.on_row_double_clicked)

        layout.addWidget(self.table)

    def add_signal(self, signal_data: dict):
        """Add signal to table"""
        # Store signal
        self.signals.insert(0, signal_data)  # Add to beginning

        # Trim to max
        if len(self.signals) > self.max_signals:
            self.signals = self.signals[:self.max_signals]

        # Add row at top
        self.table.insertRow(0)

        # Time
        timestamp = signal_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()

        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self.table.setItem(0, 0, QTableWidgetItem(time_str))

        # Message ID
        msg_id = _clean(signal_data.get('message_id'))
        self.table.setItem(0, 1, QTableWidgetItem(str(int(msg_id)) if msg_id is not None else '--'))

        # Channel
        channel = _clean(signal_data.get('channel_username'), 'Unknown')
        self.table.setItem(0, 2, QTableWidgetItem(str(channel)))

        # Symbol
        symbol = _clean(signal_data.get('symbol'), '')
        self.table.setItem(0, 3, QTableWidgetItem(str(symbol)))

        # Direction
        direction = _clean(signal_data.get('direction'), '')
        direction_item = QTableWidgetItem(str(direction))

        # Color code direction
        if direction == 'BUY':
            direction_item.setForeground(QColor(76, 175, 80))  # Green
        elif direction == 'SELL':
            direction_item.setForeground(QColor(244, 67, 54))  # Red

        self.table.setItem(0, 4, direction_item)

        # Entry
        entry_single = _clean(signal_data.get('entry_price'))
        entry_min = _clean(signal_data.get('entry_price_min'))
        entry_max = _clean(signal_data.get('entry_price_max'))

        if entry_single is not None:
            entry_str = str(entry_single)
        elif entry_min is not None and entry_max is not None:
            entry_str = f"{entry_min}-{entry_max}"
        elif entry_min is not None:
            entry_str = str(entry_min)
        else:
            entry_str = "--"

        self.table.setItem(0, 5, QTableWidgetItem(entry_str))

        # Stop Loss
        self.table.setItem(0, 6, QTableWidgetItem(_fmt(signal_data.get('stop_loss'))))

        # Take Profits
        self.table.setItem(0, 7, QTableWidgetItem(_fmt(signal_data.get('take_profit_1'))))
        self.table.setItem(0, 8, QTableWidgetItem(_fmt(signal_data.get('take_profit_2'))))
        self.table.setItem(0, 9, QTableWidgetItem(_fmt(signal_data.get('take_profit_3'))))
        self.table.setItem(0, 10, QTableWidgetItem(_fmt(signal_data.get('take_profit_4'))))

        # Confidence
        confidence = _clean(signal_data.get('confidence_score'), 0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0
        conf_pct = int(confidence * 100)
        conf_item = QTableWidgetItem(f"{conf_pct}%")
        # Color code confidence
        if confidence >= 0.8:
            conf_item.setForeground(QColor(76, 175, 80))   # Green
        elif confidence >= 0.6:
            conf_item.setForeground(QColor(255, 152, 0))   # Orange
        else:
            conf_item.setForeground(QColor(244, 67, 54))   # Red
        self.table.setItem(0, 11, conf_item)

        # Execution Status
        exec_status = _clean(signal_data.get('execution_status'), 'PENDING')
        status_item = QTableWidgetItem(str(exec_status))
        status_colors = {
            'EXECUTED': QColor(76, 175, 80),    # Green
            'PENDING': QColor(255, 152, 0),     # Orange
            'SKIPPED': QColor(158, 158, 158),   # Gray
            'FAILED': QColor(244, 67, 54),      # Red
            'LOW_CONF': QColor(121, 85, 72),    # Brown
        }
        status_item.setForeground(status_colors.get(exec_status, QColor(255, 152, 0)))
        self.table.setItem(0, 12, status_item)

        # Limit rows in table
        if self.table.rowCount() > 50:
            self.table.removeRow(self.table.rowCount() - 1)

        # Auto-scroll to top
        self.table.scrollToTop()

    def update_signal_status(self, message_id: int, status: str):
        """Update the execution status of a signal in the table"""
        status_colors = {
            'EXECUTED': QColor(76, 175, 80),    # Green
            'PENDING': QColor(255, 152, 0),     # Orange
            'SKIPPED': QColor(158, 158, 158),   # Gray
            'FAILED': QColor(244, 67, 54),      # Red
            'LOW_CONF': QColor(121, 85, 72),    # Brown
        }

        # Update in stored signals
        for sig in self.signals:
            if sig.get('message_id') == message_id:
                sig['execution_status'] = status
                break

        # Update in table display
        for row in range(self.table.rowCount()):
            msg_item = self.table.item(row, 1)  # MsgID column
            if msg_item and msg_item.text() == str(message_id):
                status_item = QTableWidgetItem(status)
                status_item.setForeground(status_colors.get(status, QColor(255, 152, 0)))
                self.table.setItem(row, 12, status_item)
                break

    def clear_table(self):
        """Clear all signals from table"""
        self.table.setRowCount(0)
        self.signals.clear()

    def refresh(self):
        """Refresh table"""
        # Rebuild table from signals list
        self.table.setRowCount(0)
        for signal in reversed(self.signals[:50]):  # Show last 50
            self.add_signal(signal)

    def on_row_double_clicked(self, index):
        """Handle row double-click"""
        row = index.row()
        if row < len(self.signals):
            self.signal_selected.emit(self.signals[row])

    def get_all_signals(self):
        """Get all signals"""
        return self.signals
