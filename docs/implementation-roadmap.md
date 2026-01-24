# Implementation Roadmap

## Project Phases

This document outlines the step-by-step implementation plan for the Telegram Signal Extraction System.

## Phase 1: Project Setup and Foundation (Week 1)

### 1.1 Development Environment Setup

**Tasks:**
- [ ] Create project directory structure
- [ ] Initialize Git repository
- [ ] Set up Python virtual environment
- [ ] Create requirements.txt with initial dependencies
- [ ] Configure .gitignore
- [ ] Set up code formatting tools (black, pylint)

**Directory Structure:**
```
TellegramSignals/
├── docs/                      # Documentation (already created)
├── src/                       # Source code
│   ├── __init__.py
│   ├── main.py               # Application entry point
│   ├── config/               # Configuration management
│   │   ├── __init__.py
│   │   └── config_manager.py
│   ├── telegram/             # Telegram client wrapper
│   │   ├── __init__.py
│   │   └── listener.py
│   ├── extraction/           # Signal extraction logic
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   ├── patterns.py
│   │   └── validators.py
│   ├── storage/              # Data persistence
│   │   ├── __init__.py
│   │   ├── csv_writer.py
│   │   └── error_logger.py
│   └── utils/                # Utilities
│       ├── __init__.py
│       └── logging_setup.py
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_extraction.py
│   ├── test_validation.py
│   └── fixtures/             # Test data
│       └── sample_messages.py
├── config/                    # Configuration files
│   ├── config.yaml
│   └── .env.example
├── output/                    # Output files
│   └── .gitkeep
├── logs/                      # Log files
│   └── .gitkeep
├── sessions/                  # Telegram sessions
│   └── .gitkeep
├── requirements.txt
├── README.md
└── .gitignore
```

**Initial Dependencies (requirements.txt):**
```
# Telegram client
Telethon>=1.34.0

# Data handling
pandas>=2.0.0
python-dateutil>=2.8.2

# Configuration
python-dotenv>=1.0.0
PyYAML>=6.0

# Development
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
pylint>=2.17.0
```

### 1.2 Telegram API Setup

**Tasks:**
- [ ] Create Telegram account (if not exists)
- [ ] Register application at https://my.telegram.org
- [ ] Obtain API ID and API Hash
- [ ] Join target channels (@nickalphatrader, @GaryGoldLegacy)
- [ ] Create .env file with credentials

**Deliverables:**
- `.env` file with TELEGRAM_API_ID and TELEGRAM_API_HASH
- Documentation of setup process

### 1.3 Basic Configuration System

**Tasks:**
- [ ] Create config.yaml template
- [ ] Implement ConfigManager class
- [ ] Add environment variable override support
- [ ] Add configuration validation

**Code Deliverable:**
```python
# src/config/config_manager.py
class ConfigManager:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self._validate_config()

    def _load_config(self, path):
        """Load YAML and override with env vars"""
        pass

    def _validate_config(self):
        """Ensure required fields present"""
        pass

    def get(self, key, default=None):
        """Get config value"""
        pass
```

## Phase 2: Telegram Integration (Week 2)

### 2.1 Basic Telegram Client

**Tasks:**
- [ ] Implement TelegramListener class
- [ ] Add authentication flow
- [ ] Add session persistence
- [ ] Test connection to Telegram

**Code Deliverable:**
```python
# src/telegram/listener.py
class TelegramListener:
    async def authenticate(self):
        """Handle phone number authentication"""
        pass

    async def connect(self):
        """Connect to Telegram"""
        pass

    async def add_channel(self, username):
        """Subscribe to channel"""
        pass

    def on_new_message(self, callback):
        """Register message handler"""
        pass
```

**Testing:**
- Manual test: Connect and receive messages from test channel

### 2.2 Message Event Handling

**Tasks:**
- [ ] Implement event handler registration
- [ ] Add message filtering (channels only)
- [ ] Log received messages for testing
- [ ] Test with live channels

**Deliverable:**
- Working message listener that logs all new messages from target channels

### 2.3 Connection Reliability

**Tasks:**
- [ ] Implement auto-reconnection logic
- [ ] Add exponential backoff
- [ ] Add connection health monitoring
- [ ] Test network interruption scenarios

**Testing:**
- Disconnect network and verify reconnection
- Leave running for 24 hours to verify stability

## Phase 3: Signal Extraction Engine (Week 3-4)

### 3.1 Pattern Matching Foundation

**Tasks:**
- [ ] Create pattern definitions based on signal-formats.md
- [ ] Implement regex-based field extractors
- [ ] Add symbol normalization
- [ ] Create unit tests for each extractor

**Code Deliverable:**
```python
# src/extraction/patterns.py
class PatternMatcher:
    def extract_symbol(self, text):
        """Extract trading symbol"""
        pass

    def extract_direction(self, text):
        """Extract BUY/SELL"""
        pass

    def extract_entry(self, text):
        """Extract entry price or range"""
        pass

    def extract_stop_loss(self, text):
        """Extract SL level"""
        pass

    def extract_take_profits(self, text):
        """Extract all TP levels"""
        pass
```

**Test Data:**
- Use screenshots from signal-formats.md
- Create 15-20 test cases covering variations

### 3.2 Signal Extractor Implementation

**Tasks:**
- [ ] Implement SignalExtractor class
- [ ] Add is_signal() method
- [ ] Add extract_signal() method
- [ ] Implement confidence scoring
- [ ] Add extraction notes

**Code Deliverable:**
```python
# src/extraction/extractor.py
class SignalExtractor:
    def __init__(self, config):
        self.patterns = PatternMatcher()
        self.validator = SignalValidator()

    def is_signal(self, text):
        """Quick check if message is a signal"""
        pass

    def extract_signal(self, text, metadata):
        """Extract complete signal"""
        pass

    def _calculate_confidence(self, extracted_fields):
        """Score extraction quality"""
        pass
```

**Testing:**
- Unit tests with 95%+ accuracy on test corpus
- Integration test with sample messages

### 3.3 Validation Logic

**Tasks:**
- [ ] Implement price validation (SL/TP vs entry)
- [ ] Add symbol validation
- [ ] Implement confidence thresholding
- [ ] Add duplicate detection (optional)

**Code Deliverable:**
```python
# src/extraction/validators.py
class SignalValidator:
    def validate_signal(self, signal):
        """Validate signal makes trading sense"""
        pass

    def validate_prices(self, signal):
        """Check SL/TP relative to entry"""
        pass

    def validate_symbol(self, symbol):
        """Check symbol is recognized"""
        pass
```

## Phase 4: Data Storage (Week 4)

### 4.1 CSV Writer

**Tasks:**
- [ ] Implement CSVWriter class
- [ ] Add atomic write support
- [ ] Implement file locking awareness
- [ ] Add CSV rotation (if needed)
- [ ] Test with MT5 concurrent access

**Code Deliverable:**
```python
# src/storage/csv_writer.py
class CSVWriter:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self._ensure_header()

    def write_signal(self, signal):
        """Write signal to CSV"""
        pass

    def _atomic_write(self, data):
        """Write with temp file + rename"""
        pass
```

**Testing:**
- Write 100+ signals
- Verify MT5 can read CSV
- Test file locking scenarios

### 4.2 Error Logging

**Tasks:**
- [ ] Implement ErrorLogger class
- [ ] Create JSONL format logger
- [ ] Add structured error categorization
- [ ] Implement log rotation

**Code Deliverable:**
```python
# src/storage/error_logger.py
class ErrorLogger:
    def log_extraction_error(self, message, channel, reason):
        """Log failed extraction"""
        pass

    def log_system_error(self, error, context):
        """Log system errors"""
        pass
```

### 4.3 System Logging

**Tasks:**
- [ ] Configure Python logging module
- [ ] Set up file and console handlers
- [ ] Implement log rotation
- [ ] Add logging throughout application

**Deliverable:**
- Comprehensive logging in all components

## Phase 5: Integration and Testing (Week 5)

### 5.1 End-to-End Integration

**Tasks:**
- [ ] Implement main application loop
- [ ] Connect all components
- [ ] Add graceful shutdown handling
- [ ] Test complete flow

**Code Deliverable:**
```python
# src/main.py
async def main():
    """Main application entry point"""
    # Load config
    # Initialize components
    # Register handlers
    # Start monitoring
    # Run until interrupted
    pass

if __name__ == '__main__':
    asyncio.run(main())
```

### 5.2 Test Corpus Creation

**Tasks:**
- [ ] Collect 50+ real messages from channels
- [ ] Manually label expected extractions
- [ ] Create test fixtures
- [ ] Implement accuracy metrics

**Deliverable:**
- Test corpus with ground truth labels
- Automated test suite

### 5.3 Accuracy Testing

**Tasks:**
- [ ] Run extractor on test corpus
- [ ] Measure accuracy per field
- [ ] Identify failure patterns
- [ ] Refine extraction patterns
- [ ] Iterate until >95% accuracy

**Metrics:**
```
Target Metrics:
- Symbol extraction: >98% accuracy
- Direction extraction: >98% accuracy
- Entry extraction: >95% accuracy
- SL extraction: >90% accuracy
- TP extraction: >90% accuracy
- Overall signal extraction: >95% accuracy
```

### 5.4 Load Testing

**Tasks:**
- [ ] Test with high message volume
- [ ] Verify memory stability (24hr run)
- [ ] Check CSV file growth
- [ ] Validate no message loss

**Testing Scenarios:**
- 100 signals in 1 hour
- 24-hour continuous operation
- Network interruption recovery

## Phase 6: GUI Development (Week 6)

### 6.1 Basic GUI Framework Setup

**Tasks:**
- [ ] Install PySide6 and dependencies
- [ ] Create main window class structure
- [ ] Set up application icon and resources
- [ ] Implement basic window layout with placeholders
- [ ] Test GUI startup and shutdown

**Code Deliverable:**
```python
# src/gui/main_window.py
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Telegram Signal Extractor")
        self.setGeometry(100, 100, 1024, 768)
        # Setup central widget and layouts
        pass

# src/gui/app.py
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### 6.2 System Tray Integration

**Tasks:**
- [ ] Create system tray icon with status indicator
- [ ] Implement tray context menu
- [ ] Add minimize to tray functionality
- [ ] Implement tray icon click to show/hide window
- [ ] Create status icons (green/yellow/red/gray)

**Code Deliverable:**
```python
# src/gui/system_tray.py
class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_menu()
        self.setIcon(self.get_status_icon('green'))

    def setup_menu(self):
        menu = QMenu()
        show_action = menu.addAction("Show Window")
        menu.addSeparator()
        recent_menu = menu.addMenu("Recent Signals")
        menu.addSeparator()
        menu.addAction("Settings...")
        menu.addAction("Exit")
        self.setContextMenu(menu)

    def update_status(self, status: str):
        # green, yellow, red, gray
        self.setIcon(self.get_status_icon(status))
```

### 6.3 Dashboard Implementation

**Tasks:**
- [ ] Create connection status indicator
- [ ] Implement channel list widget
- [ ] Build signal table widget
- [ ] Add metrics display (messages/signals/errors)
- [ ] Implement activity log widget
- [ ] Connect to backend data sources

**Layout Structure:**
- Left panel: Channels and metrics
- Center panel: Signal table
- Bottom panel: Activity log
- Top: Status bar with connection info

### 6.4 Threading and Background Worker

**Tasks:**
- [ ] Create QThread-based background worker
- [ ] Implement Qt signals for thread-safe communication
- [ ] Connect Telegram client to worker thread
- [ ] Test signal/slot communication between threads
- [ ] Ensure UI remains responsive during processing

**Code Deliverable:**
```python
# src/gui/worker.py
class BackgroundWorker(QThread):
    signal_extracted = pyqtSignal(dict)  # Emit when signal extracted
    error_occurred = pyqtSignal(str)     # Emit on error
    status_changed = pyqtSignal(str)     # Emit on status change

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True

    def run(self):
        # Run asyncio event loop in thread
        asyncio.run(self.main_loop())

    async def main_loop(self):
        # Initialize Telegram client
        # Start monitoring
        # Emit signals on events
        pass

    def stop(self):
        self.running = False
```

### 6.5 Settings Dialog

**Tasks:**
- [ ] Create multi-tab settings dialog
- [ ] Implement Telegram credentials section
- [ ] Add channel management (add/remove)
- [ ] Create extraction settings controls
- [ ] Add GUI preferences (theme, notifications)
- [ ] Implement save/load settings

**Tabs:**
1. Telegram: API credentials, session
2. Channels: List with enable/disable, add/remove
3. Extraction: Confidence threshold, pattern settings
4. Output: File paths, CSV options
5. GUI: Theme, notifications, auto-start

### 6.6 Notification System

**Tasks:**
- [ ] Implement desktop notification manager
- [ ] Create notification for new signals
- [ ] Add notification for errors
- [ ] Make notifications dismissible
- [ ] Add notification preferences
- [ ] Test notifications on Windows

**Code Deliverable:**
```python
# src/gui/notifications.py
class NotificationManager:
    def __init__(self, tray_icon):
        self.tray_icon = tray_icon
        self.enabled = True

    def show_signal_notification(self, signal):
        if self.enabled:
            title = f"New {signal['direction']} Signal"
            message = f"{signal['symbol']} @ {signal['entry_price']}"
            self.tray_icon.showMessage(
                title, message,
                QSystemTrayIcon.Information,
                3000  # 3 seconds
            )
```

### 6.7 Error Log Viewer

**Tasks:**
- [ ] Create error log dialog
- [ ] Display failed extractions in table
- [ ] Add retry extraction button
- [ ] Implement mark as reviewed
- [ ] Add export to file functionality

### 6.8 Integration with Core System

**Tasks:**
- [ ] Connect AppController to GUI
- [ ] Wire up start/stop monitoring buttons
- [ ] Connect signal extraction events to UI updates
- [ ] Implement real-time status updates
- [ ] Test end-to-end GUI ↔ Backend communication

**Code Deliverable:**
```python
# src/gui/controller.py
class AppController(QObject):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.worker = BackgroundWorker(config)
        self.main_window = MainWindow(self)
        self.setup_connections()

    def setup_connections(self):
        # Connect worker signals to UI slots
        self.worker.signal_extracted.connect(
            self.main_window.on_new_signal
        )
        self.worker.status_changed.connect(
            self.main_window.update_status
        )

    def start_monitoring(self):
        self.worker.start()

    def stop_monitoring(self):
        self.worker.stop()
        self.worker.wait()
```

### 6.9 Testing and Polish

**Tasks:**
- [ ] Test all GUI interactions
- [ ] Verify thread safety
- [ ] Test minimize/restore from tray
- [ ] Test notifications
- [ ] Test settings persistence
- [ ] Fix UI bugs and polish appearance
- [ ] Test on different Windows versions

**Deliverable:**
- Fully functional GUI application
- All features tested and working
- Smooth user experience

## Phase 7: MT5 Integration (Week 7)

### 6.1 MT5 EA Development

**Tasks:**
- [ ] Create basic MT5 EA to read CSV
- [ ] Implement CSV parsing in MQL5
- [ ] Add signal processing logic
- [ ] Test with sample signals

**MQL5 Code Structure:**
```mql5
// MT5 Expert Advisor
void OnTick() {
    CheckForNewSignals();
}

void CheckForNewSignals() {
    // Read CSV
    // Find unprocessed signals
    // Execute trades
    // Mark as processed
}
```

### 6.2 Integration Testing

**Tasks:**
- [ ] Run Python extractor + MT5 EA simultaneously
- [ ] Verify signal flow: Telegram → CSV → MT5
- [ ] Test edge cases (file locking, etc.)
- [ ] Validate trade execution

**Testing:**
- End-to-end flow with real signals
- Verify no data loss
- Check timing (latency from Telegram to MT5)

## Phase 8: Deployment and Monitoring (Week 8)

### 8.1 Application Packaging

**Tasks:**
- [ ] Create PyInstaller spec file
- [ ] Package application as standalone .exe
- [ ] Include all dependencies and resources
- [ ] Test .exe on clean Windows installation
- [ ] Create installer (optional - use Inno Setup)

**PyInstaller Commands:**
```bash
# Create spec file
pyinstaller --name="TelegramSignalExtractor" ^
            --windowed ^
            --onefile ^
            --icon=assets/icon.ico ^
            --add-data="config;config" ^
            --add-data="assets;assets" ^
            src/gui/app.py

# Build from spec
pyinstaller TelegramSignalExtractor.spec
```

**Deliverable:**
- Single executable file (TelegramSignalExtractor.exe)
- Optional: Windows installer (.msi or .exe)

### 8.2 Production Deployment

**Tasks:**
- [ ] Create deployment documentation
- [ ] Set up production environment
- [ ] Configure logging for production
- [ ] Set up backup/restore procedures
- [ ] Create shortcuts for auto-start

**Deliverables:**
- Deployment guide
- Backup script
- Recovery procedures
- Startup shortcut for Windows Startup folder

### 8.3 Auto-Start Configuration

**Tasks:**
- [ ] Install NSSM (Non-Sucking Service Manager)
- [ ] Create service configuration
- [ ] Test auto-start on reboot
- [ ] Configure service recovery options

**Commands:**
```bash
# Install as Windows service
nssm install TelegramSignalExtractor
nssm set TelegramSignalExtractor Application "C:\path\to\venv\python.exe"
nssm set TelegramSignalExtractor AppParameters "C:\path\to\src\main.py"
nssm set TelegramSignalExtractor AppDirectory "C:\path\to\TellegramSignals"
nssm start TelegramSignalExtractor
```

### 8.4 Monitoring Setup

**Tasks:**
- [ ] Implement health check endpoint (optional)
- [ ] Set up log monitoring
- [ ] Create dashboard (future)
- [ ] Configure alerts (optional)

**Monitoring Checklist:**
- Log file rotation working
- CSV file growing appropriately
- No error spikes in logs
- System resource usage acceptable

### 8.5 Documentation Finalization

**Tasks:**
- [ ] Write README.md
- [ ] Create user guide
- [ ] Document troubleshooting steps
- [ ] Add FAQ section

## Phase 9: Optimization and Enhancement (Ongoing)

### 8.1 Pattern Refinement

**Tasks:**
- [ ] Monitor extraction accuracy
- [ ] Collect failed extractions
- [ ] Update patterns as needed
- [ ] Add new channel formats

**Process:**
1. Weekly review of error logs
2. Identify common failure patterns
3. Update regex patterns
4. Test against corpus
5. Deploy updates

### 8.2 Performance Optimization

**Tasks:**
- [ ] Profile application
- [ ] Optimize hot paths
- [ ] Reduce memory footprint
- [ ] Improve CSV write performance

### 8.3 Feature Additions (Future)

**Potential Enhancements:**
- [ ] Web dashboard for monitoring
- [ ] Email/SMS alerts
- [ ] Multiple output formats (DB, API)
- [ ] Signal analytics and reporting
- [ ] Machine learning for extraction
- [ ] Image-based signal extraction (OCR)

## Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Telegram API rate limiting | High | Implement rate limiting, monitor API usage |
| Session expiration | Medium | Auto-reauth, alerts on failure |
| CSV file corruption | High | Atomic writes, regular backups |
| Network instability | Medium | Auto-reconnect, buffering |
| MT5 file locking | Medium | Retry logic, separate processed file |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Channel format changes | High | Monitor accuracy, quick update process |
| Telegram account ban | Critical | Follow ToS, avoid automation abuse |
| Disk space exhaustion | Medium | Log rotation, monitoring |
| System crashes | Medium | Run as service, auto-restart |

## Success Criteria

### MVP (Minimum Viable Product) - End of Phase 6

- [ ] Successfully authenticate with Telegram
- [ ] Monitor 2 channels (nickalphatrader, GaryGoldLegacy)
- [ ] Extract signals with >90% accuracy
- [ ] Write signals to CSV in correct format
- [ ] MT5 EA can read and process signals
- [ ] System runs continuously for 7 days without intervention
- [ ] All errors logged appropriately

### Production Ready - End of Phase 7

- [ ] Extraction accuracy >95%
- [ ] Zero data loss over 30 days
- [ ] Auto-recovery from all common failures
- [ ] Complete documentation
- [ ] Runs as Windows service
- [ ] Tested with 100+ real signals

## Timeline Summary

| Phase | Duration | Key Deliverable |
|-------|----------|----------------|
| Phase 1: Setup | Week 1 | Project structure, config system |
| Phase 2: Telegram | Week 2 | Working message listener |
| Phase 3: Extraction | Week 3-4 | Signal extraction engine |
| Phase 4: Storage | Week 4 | CSV writer, error logger |
| Phase 5: Testing | Week 5 | Tested, accurate system |
| Phase 6: GUI | Week 6 | Desktop app with system tray |
| Phase 7: MT5 | Week 7 | End-to-end integration |
| Phase 8: Deployment | Week 8 | Production deployment |
| Phase 9: Ongoing | Continuous | Optimization, enhancements |

**Total Time to MVP (Console)**: 5 weeks
**Total Time to MVP (Desktop App)**: 6 weeks
**Total Time to Production**: 8-9 weeks

## Development Best Practices

### Code Quality
- Write docstrings for all functions
- Maintain >80% test coverage
- Use type hints
- Follow PEP 8 style guide
- Code review before merging

### Version Control
- Commit frequently with clear messages
- Use feature branches
- Tag releases
- Maintain CHANGELOG.md

### Testing Strategy
- Write tests before or alongside code (TDD)
- Test edge cases
- Integration tests for critical flows
- Manual testing with real data

### Security
- Never commit .env or session files
- Use environment variables in production
- Regular security audits
- Keep dependencies updated

## Support and Maintenance

### Daily Tasks
- Check system logs for errors
- Verify CSV file is growing
- Monitor extraction accuracy

### Weekly Tasks
- Review error logs
- Update extraction patterns if needed
- Check disk space
- Verify backup system

### Monthly Tasks
- Update dependencies
- Review and archive old logs
- Performance review
- Feature planning

## Conclusion

This roadmap provides a structured approach to building the Telegram Signal Extraction System. Follow the phases sequentially, ensuring each phase is complete before moving to the next. Adjust timeline as needed based on complexity and testing results.

**Next Steps:**
1. Review and approve this roadmap
2. Set up development environment (Phase 1.1)
3. Create Telegram API credentials (Phase 1.2)
4. Begin implementation following the phase sequence
