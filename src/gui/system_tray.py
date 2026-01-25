"""System tray icon and menu"""
from pathlib import Path
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, Signal


class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with context menu"""

    # Signals
    show_window_requested = Signal()
    exit_requested = Signal()
    monitoring_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.monitoring_enabled = False

        # Load app icon
        self._load_app_icon()

        # Set initial icon
        self.set_icon_color('gray')

        # Set up context menu
        self.setup_menu()

        # Connect activation
        self.activated.connect(self.on_activated)

    def _load_app_icon(self):
        """Load the application icon from resources"""
        icon_path = Path(__file__).parent / "resources" / "icons" / "tray.png"
        if icon_path.exists():
            self._base_icon = QPixmap(str(icon_path))
        else:
            # Fallback: create a simple icon
            self._base_icon = None

    def setup_menu(self):
        """Create context menu"""
        menu = QMenu()

        # Status label (not clickable)
        self.status_label = QAction("● Telegram Signal Extractor", self)
        self.status_label.setEnabled(False)
        menu.addAction(self.status_label)

        menu.addSeparator()

        # Show window
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)

        menu.addSeparator()

        # Recent signals submenu
        self.recent_signals_menu = QMenu("Recent Signals", menu)
        self.update_recent_signals([])  # Empty initially
        menu.addMenu(self.recent_signals_menu)

        menu.addSeparator()

        # Start/Stop monitoring
        self.monitoring_action = QAction("Start Monitoring", self)
        self.monitoring_action.setCheckable(True)
        self.monitoring_action.triggered.connect(self.toggle_monitoring)
        menu.addAction(self.monitoring_action)

        menu.addSeparator()

        # Open logs and CSV
        open_logs_action = QAction("Open Logs Folder", self)
        open_logs_action.triggered.connect(self.open_logs)
        menu.addAction(open_logs_action)

        open_csv_action = QAction("Open Output CSV", self)
        open_csv_action.triggered.connect(self.open_csv)
        menu.addAction(open_csv_action)

        menu.addSeparator()

        # Settings
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)

        # About
        about_action = QAction("About...", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)

        menu.addSeparator()

        # Exit
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

    def set_icon_color(self, color: str):
        """Set tray icon with status indicator overlay"""
        # Color mapping for status indicator
        color_map = {
            'green': QColor(76, 175, 80),      # Connected
            'yellow': QColor(255, 193, 7),     # Warning
            'red': QColor(244, 67, 54),        # Error
            'gray': QColor(158, 158, 158)      # Stopped
        }

        size = 32
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the base app icon if available
        if self._base_icon:
            scaled_icon = self._base_icon.scaled(
                size, size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled_icon)
        else:
            # Fallback: draw a simple golden diamond
            painter.setBrush(QColor(218, 165, 32))
            painter.setPen(Qt.NoPen)
            points = [
                (size // 2, 4),
                (size - 4, size // 2),
                (size // 2, size - 4),
                (4, size // 2)
            ]
            from PySide6.QtGui import QPolygon
            from PySide6.QtCore import QPoint
            polygon = QPolygon([QPoint(x, y) for x, y in points])
            painter.drawPolygon(polygon)

        # Draw status indicator dot in bottom-right corner
        indicator_size = 10
        indicator_x = size - indicator_size - 1
        indicator_y = size - indicator_size - 1

        # Draw indicator background (dark border)
        painter.setBrush(QColor(0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(indicator_x - 1, indicator_y - 1, indicator_size + 2, indicator_size + 2)

        # Draw colored indicator
        painter.setBrush(color_map.get(color, QColor(158, 158, 158)))
        painter.drawEllipse(indicator_x, indicator_y, indicator_size, indicator_size)

        painter.end()

        self.setIcon(QIcon(pixmap))

    def update_status(self, status: str):
        """Update tray icon based on status"""
        status_lower = status.lower()

        if status_lower == 'connected':
            self.set_icon_color('green')
            self.status_label.setText("● Connected")
        elif status_lower == 'warning':
            self.set_icon_color('yellow')
            self.status_label.setText("● Warning")
        elif status_lower == 'error':
            self.set_icon_color('red')
            self.status_label.setText("● Error")
        else:
            self.set_icon_color('gray')
            self.status_label.setText("● Stopped")

        # Update tooltip
        self.setToolTip(f"Telegram Signal Extractor - {status}")

    def update_monitoring_state(self, enabled: bool):
        """Update monitoring action state"""
        self.monitoring_enabled = enabled
        self.monitoring_action.setChecked(enabled)
        self.monitoring_action.setText("Stop Monitoring" if enabled else "Start Monitoring")

    def update_recent_signals(self, signals: list):
        """Update recent signals submenu"""
        self.recent_signals_menu.clear()

        if not signals:
            no_signals_action = QAction("No recent signals", self)
            no_signals_action.setEnabled(False)
            self.recent_signals_menu.addAction(no_signals_action)
        else:
            # Show last 5 signals
            for signal in signals[:5]:
                signal_text = f"{signal.get('time', '')} - {signal.get('symbol', '')} {signal.get('direction', '')} @ {signal.get('entry', '')}"
                action = QAction(signal_text, self)
                action.triggered.connect(lambda s=signal: self.show_signal_details(s))
                self.recent_signals_menu.addAction(action)

            self.recent_signals_menu.addSeparator()

            # Show all signals
            show_all_action = QAction("Show All...", self)
            show_all_action.triggered.connect(self.show_all_signals)
            self.recent_signals_menu.addAction(show_all_action)

    # Signal handlers
    def on_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:  # Left click
            self.show_window()
        elif reason == QSystemTrayIcon.DoubleClick:  # Double click
            self.show_window()

    def show_window(self):
        """Show main window"""
        if self.parent_window:
            self.parent_window.show()
            self.parent_window.raise_()
            self.parent_window.activateWindow()
        self.show_window_requested.emit()

    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        self.monitoring_enabled = not self.monitoring_enabled
        self.monitoring_toggled.emit(self.monitoring_enabled)
        self.update_monitoring_state(self.monitoring_enabled)

    def open_logs(self):
        """Open logs folder"""
        if self.parent_window:
            self.parent_window.open_logs_folder()

    def open_csv(self):
        """Open CSV file"""
        if self.parent_window:
            self.parent_window.open_csv_file()

    def show_settings(self):
        """Show settings dialog"""
        if self.parent_window:
            self.parent_window.show_settings()
            self.show_window()

    def show_about(self):
        """Show about dialog"""
        if self.parent_window:
            self.parent_window.show_about()
            self.show_window()

    def show_signal_details(self, signal: dict):
        """Show signal details"""
        # TODO: Implement signal details dialog
        self.show_window()

    def show_all_signals(self):
        """Show all signals"""
        self.show_window()

    def exit_application(self):
        """Exit the application"""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            None,
            "Exit Application",
            "Are you sure you want to exit?\nMonitoring will stop.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.exit_requested.emit()

    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show desktop notification"""
        self.showMessage(title, message, QSystemTrayIcon.Information, duration)
