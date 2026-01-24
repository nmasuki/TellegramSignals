"""Signal table widget"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from datetime import datetime


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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Time", "Channel", "Symbol", "Direction", "Entry", "SL", "TP1"
        ])

        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Time
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Channel
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Symbol
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Direction
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Entry
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # SL
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # TP1

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

        time_str = timestamp.strftime("%H:%M:%S")
        self.table.setItem(0, 0, QTableWidgetItem(time_str))

        # Channel
        channel = signal_data.get('channel_username', 'Unknown')
        self.table.setItem(0, 1, QTableWidgetItem(channel))

        # Symbol
        symbol = signal_data.get('symbol', '')
        self.table.setItem(0, 2, QTableWidgetItem(symbol))

        # Direction
        direction = signal_data.get('direction', '')
        direction_item = QTableWidgetItem(direction)

        # Color code direction
        if direction == 'BUY':
            direction_item.setForeground(QColor(76, 175, 80))  # Green
        elif direction == 'SELL':
            direction_item.setForeground(QColor(244, 67, 54))  # Red

        self.table.setItem(0, 3, direction_item)

        # Entry
        entry_min = signal_data.get('entry_price_min')
        entry_max = signal_data.get('entry_price_max')
        entry_single = signal_data.get('entry_price')

        if entry_single:
            entry_str = f"{entry_single}"
        elif entry_min and entry_max:
            entry_str = f"{entry_min}-{entry_max}"
        elif entry_min:
            entry_str = f"{entry_min}"
        else:
            entry_str = "--"

        self.table.setItem(0, 4, QTableWidgetItem(entry_str))

        # Stop Loss
        sl = signal_data.get('stop_loss', '')
        self.table.setItem(0, 5, QTableWidgetItem(str(sl) if sl else '--'))

        # Take Profit 1
        tp1 = signal_data.get('take_profit_1', '')
        self.table.setItem(0, 6, QTableWidgetItem(str(tp1) if tp1 else '--'))

        # Limit rows in table
        if self.table.rowCount() > 50:
            self.table.removeRow(self.table.rowCount() - 1)

        # Auto-scroll to top
        self.table.scrollToTop()

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
