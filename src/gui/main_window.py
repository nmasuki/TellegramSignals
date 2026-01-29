"""Main application window"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QStatusBar, QMenuBar, QMenu,
    QSystemTrayIcon
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from src.gui.widgets.channel_widget import ChannelWidget
from src.gui.widgets.metrics_widget import MetricsWidget
from src.gui.widgets.signal_table import SignalTableWidget
from src.gui.widgets.activity_log import ActivityLogWidget
from src.gui.system_tray import SystemTrayIcon


class MainWindow(QMainWindow):
    """Main application window"""

    # Signals
    start_monitoring = Signal()
    stop_monitoring = Signal()
    settings_requested = Signal()
    exit_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram Signal Extractor")
        self.setGeometry(100, 100, 1024, 768)
        self.setMinimumSize(800, 600)

        # Flag for actual exit vs minimize to tray
        self.force_close = False

        # Initialize UI components
        self.setup_menu_bar()
        self.setup_ui()
        self.setup_status_bar()
        self.setup_system_tray()

    def setup_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_csv_action = QAction("&Open CSV File", self)
        open_csv_action.triggered.connect(self.open_csv_file)
        file_menu.addAction(open_csv_action)

        open_logs_action = QAction("Open &Logs Folder", self)
        open_logs_action.triggered.connect(self.open_logs_folder)
        file_menu.addAction(open_logs_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.exit_requested.emit)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        settings_action = QAction("&Preferences...", self)
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        refresh_action = QAction("&Refresh", self)
        refresh_action.triggered.connect(self.refresh_view)
        view_menu.addAction(refresh_action)

        view_menu.addSeparator()

        clear_log_action = QAction("Clear Activity &Log", self)
        clear_log_action.triggered.connect(self.clear_activity_log)
        view_menu.addAction(clear_log_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        docs_action = QAction("&Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)

    def setup_ui(self):
        """Set up the main UI layout"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Status panel at top
        status_panel = self.create_status_panel()
        main_layout.addWidget(status_panel)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel (channels and metrics)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel (signals and activity)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setStretchFactor(0, 1)  # Left: 25%
        splitter.setStretchFactor(1, 3)  # Right: 75%

        main_layout.addWidget(splitter)

    def create_status_panel(self):
        """Create top status panel"""
        panel = QWidget()
        panel.setStyleSheet("background-color: #f0f0f0; border: 1px solid #d0d0d0;")
        panel.setFixedHeight(50)

        layout = QHBoxLayout(panel)

        # Connection status
        self.status_indicator = QLabel("● Disconnected")
        self.status_indicator.setStyleSheet("color: gray; font-weight: bold;")
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_indicator)

        layout.addSpacing(20)

        # Uptime
        self.uptime_label = QLabel("00:00:00")
        layout.addWidget(QLabel("Uptime:"))
        layout.addWidget(self.uptime_label)

        layout.addSpacing(20)

        # Signal count
        self.signal_count_label = QLabel("0")
        layout.addWidget(QLabel("Signals:"))
        layout.addWidget(self.signal_count_label)

        layout.addStretch()

        return panel

    def create_left_panel(self):
        """Create left panel with channels and metrics"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Channel widget (grows with window)
        self.channel_widget = ChannelWidget()
        layout.addWidget(self.channel_widget, 1)  # Stretch factor 1 = grows

        # Metrics widget (fixed size)
        self.metrics_widget = MetricsWidget()
        layout.addWidget(self.metrics_widget, 0)  # Stretch factor 0 = fixed

        return panel

    def create_right_panel(self):
        """Create right panel with signals and activity"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Signal table
        self.signal_table = SignalTableWidget()
        layout.addWidget(self.signal_table, 2)  # 2/3 of space

        # Activity log
        self.activity_log = ActivityLogWidget()
        layout.addWidget(self.activity_log, 1)  # 1/3 of space

        return panel

    def setup_status_bar(self):
        """Create status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.status_message = QLabel("Ready")
        status_bar.addWidget(self.status_message)

        status_bar.addPermanentWidget(QLabel("  |  "))

        self.csv_path_label = QLabel("CSV: output/signals.csv")
        status_bar.addPermanentWidget(self.csv_path_label)

    def setup_system_tray(self):
        """Set up system tray icon"""
        self.tray_icon = SystemTrayIcon(self)
        self.tray_icon.show()

    def update_status(self, status: str, color: str = "gray"):
        """Update connection status indicator"""
        color_map = {
            "connected": "green",
            "warning": "orange",
            "error": "red",
            "stopped": "gray"
        }

        display_color = color_map.get(status.lower(), color)
        display_text = status.capitalize()

        self.status_indicator.setText(f"● {display_text}")
        self.status_indicator.setStyleSheet(f"color: {display_color}; font-weight: bold;")

        # Update tray icon
        if hasattr(self, 'tray_icon'):
            self.tray_icon.update_status(status)

    def update_uptime(self, uptime: str):
        """Update uptime display"""
        self.uptime_label.setText(uptime)

    def update_signal_count(self, count: int):
        """Update signal count"""
        self.signal_count_label.setText(str(count))

    def update_status_message(self, message: str):
        """Update status bar message"""
        self.status_message.setText(message)

    def add_signal_to_table(self, signal_data: dict):
        """Add signal to table"""
        self.signal_table.add_signal(signal_data)

    def add_activity_log(self, message: str, level: str = "info"):
        """Add message to activity log"""
        self.activity_log.add_message(message, level)

    # Menu action handlers
    def open_csv_file(self):
        """Open CSV file in default application"""
        import subprocess
        import os
        from pathlib import Path

        csv_path = Path("output/signals.csv")
        if csv_path.exists():
            if os.name == 'nt':  # Windows
                os.startfile(str(csv_path))
            else:  # macOS and Linux
                subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', str(csv_path)))

    def open_logs_folder(self):
        """Open logs folder"""
        import subprocess
        import os
        from pathlib import Path

        logs_path = Path("logs")
        logs_path.mkdir(exist_ok=True)

        if os.name == 'nt':  # Windows
            os.startfile(str(logs_path))
        else:
            subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', str(logs_path)))

    def show_settings(self):
        """Show settings dialog"""
        self.settings_requested.emit()

    def refresh_view(self):
        """Refresh all views"""
        self.channel_widget.refresh()
        self.metrics_widget.refresh()
        self.signal_table.refresh()

    def clear_activity_log(self):
        """Clear activity log"""
        self.activity_log.clear()

    def show_about(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About Telegram Signal Extractor",
            "<h3>Telegram Signal Extractor v1.0</h3>"
            "<p>Monitors Telegram channels and extracts trading signals.</p>"
            "<p><b>Status:</b> Production Ready (Phase 6 - Desktop GUI)</p>"
            "<p><b>Author:</b> Nelson Masuki</p>"
            "<p><b>Date:</b> 2026-01-24</p>"
        )

    def show_documentation(self):
        """Open documentation"""
        import webbrowser
        from pathlib import Path

        readme_path = Path("README.md")
        if readme_path.exists():
            webbrowser.open(str(readme_path.absolute()))

    def closeEvent(self, event):
        """Handle window close event"""
        if self.force_close:
            # Actually close the application
            event.accept()
        else:
            # Minimize to tray instead of closing
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Telegram Signal Extractor",
                "Application minimized to tray. Right-click the tray icon to exit.",
                QSystemTrayIcon.Information,
                2000
            )
