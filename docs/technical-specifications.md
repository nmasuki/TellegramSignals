# Technical Specifications

## 1. System Architecture

### 1.1 Component Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Signal Extractor                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌───────────────┐      ┌──────────┐ │
│  │   Telegram   │────▶ │    Signal     │────▶ │   CSV    │ │
│  │   Listener   │      │   Extractor   │      │  Writer  │ │
│  └──────────────┘      └───────────────┘      └──────────┘ │
│         │                      │                     │       │
│         ▼                      ▼                     ▼       │
│  ┌──────────────┐      ┌───────────────┐      ┌──────────┐ │
│  │   Session    │      │  Error Logger │      │  Config  │ │
│  │   Manager    │      │               │      │  Manager │ │
│  └──────────────┘      └───────────────┘      └──────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   MT5 EA        │
                    │ (Reads CSV)     │
                    └─────────────────┘
```

### 1.2 Technology Stack

#### Programming Language
- **Primary**: Python 3.9+
- **Rationale**:
  - Excellent Telegram library support (Telethon/Pyrogram)
  - Rich NLP/text processing libraries
  - Easy MT5 integration
  - Cross-platform compatibility

#### Core Libraries
- **Telegram Client**: `Telethon` or `Pyrogram`
  - Telethon: More mature, better documentation
  - Pyrogram: Modern async API, easier to use
  - **Recommendation**: Start with Telethon for stability
- **Text Processing**: `re` (regex), `dateutil`
- **Data Handling**: `pandas` for CSV operations
- **Configuration**: `python-dotenv`, `PyYAML`
- **Logging**: Built-in `logging` module

#### GUI Framework
- **Desktop GUI**: `PySide6` or `PyQt6`
  - **Recommendation**: PySide6 (official Qt for Python, LGPL license)
  - Excellent Windows integration
  - Native system tray support
  - Professional appearance
  - Rich widget library
  - Good threading support for async operations
- **System Tray**: Built-in with PySide6/PyQt6
- **Notifications**: `plyer` or native Qt notifications
- **Icons**: `qtawesome` for icon fonts or custom PNG/ICO files

#### Alternative GUI Options (Not Recommended)
- **tkinter + pystray**: Lighter weight but less professional appearance
- **wxPython**: Native look but more complex for modern UIs
- **Kivy**: Better for mobile, overkill for desktop

#### Development Tools
- **Version Control**: Git
- **Dependency Management**: `pip` + `requirements.txt` or `poetry`
- **Testing**: `pytest`
- **Code Quality**: `pylint`, `black` (formatter)
- **Packaging**: `PyInstaller` or `cx_Freeze` for standalone .exe

## 2. Detailed Component Specifications

### 2.1 Telegram Listener

**Responsibilities:**
- Authenticate with Telegram API
- Maintain persistent connection to Telegram
- Monitor specified channels for new messages
- Handle reconnection on network failures

**Key Methods:**
```python
class TelegramListener:
    def authenticate(phone: str) -> Session
    def connect() -> None
    def add_channel(channel_url: str) -> None
    def on_new_message(callback: Callable) -> None
    def disconnect() -> None
```

**Configuration:**
- API ID and API Hash (obtained from my.telegram.org)
- Phone number for authentication
- Session file path
- List of channel usernames/IDs

### 2.2 Signal Extractor

**Responsibilities:**
- Parse message text to identify trade signals
- Extract structured data fields
- Validate extracted data
- Handle multiple signal formats

**Key Methods:**
```python
class SignalExtractor:
    def is_signal(message: str) -> bool
    def extract_signal(message: str, metadata: dict) -> Signal
    def extract_symbol(text: str) -> str
    def extract_direction(text: str) -> str  # BUY/SELL
    def extract_entry(text: str) -> float | tuple
    def extract_stop_loss(text: str) -> float
    def extract_take_profits(text: str) -> list[float]
```

**Extraction Patterns:**
Signal messages typically follow patterns like:
```
GOLD
BUY @ 2045.50
SL: 2040.00
TP1: 2050.00
TP2: 2055.00
TP3: 2060.00
```

or

```
🔥 EUR/USD SELL SIGNAL
Entry: 1.0850-1.0900
Stop Loss: 1.0950
Take Profit: 1.0750
```

**Pattern Strategy:**
1. Use regex patterns for structured signals
2. Implement fallback keyword search for flexible formats
3. Maintain pattern library that can be updated per channel

### 2.3 CSV Writer

**Responsibilities:**
- Format signal data for CSV output
- Append to existing CSV file (or create new)
- Handle file locking for MT5 compatibility
- Ensure data integrity

**Key Methods:**
```python
class CSVWriter:
    def __init__(file_path: str)
    def write_signal(signal: Signal) -> None
    def write_batch(signals: list[Signal]) -> None
    def get_last_written_id() -> int
```

**File Handling:**
- Use atomic writes (write to temp, then rename)
- Include file locking mechanism
- Implement rotation if file size exceeds threshold

### 2.4 Error Logger

**Responsibilities:**
- Log messages that failed extraction
- Record system errors and exceptions
- Provide structured error information for debugging

**Key Methods:**
```python
class ErrorLogger:
    def log_extraction_error(message: str, channel: str, reason: str) -> None
    def log_system_error(error: Exception, context: dict) -> None
```

**Log Format:**
- Timestamp
- Error type
- Channel name
- Original message content
- Stack trace (for system errors)
- Extraction attempt details

### 2.5 Configuration Manager

**Responsibilities:**
- Load configuration from files/environment
- Validate configuration
- Provide configuration access to other components

**Configuration File Structure (config.yaml):**
```yaml
telegram:
  api_id: ${TELEGRAM_API_ID}
  api_hash: ${TELEGRAM_API_HASH}
  phone: ${TELEGRAM_PHONE}
  session_file: "sessions/telegram.session"

channels:
  - url: "https://t.me/nickalphatrader"
    username: "nickalphatrader"
    enabled: true
  - url: "https://t.me/GaryGoldLegacy"
    username: "GaryGoldLegacy"
    enabled: true

output:
  csv_file: "output/signals.csv"
  error_log: "logs/errors.log"
  system_log: "logs/system.log"

extraction:
  confidence_threshold: 0.7
  require_all_fields: false  # Write partial data if some fields missing

monitoring:
  heartbeat_interval: 300  # seconds
  max_reconnect_attempts: 5
  reconnect_delay: 30  # seconds

gui:
  theme: "light"  # light or dark
  window_size: [1024, 768]
  enable_notifications: true
  notification_sound: false
  start_minimized: false
  auto_start: false
  refresh_interval: 1000  # ms for UI updates
```

### 2.6 GUI Manager (Desktop Application)

**Responsibilities:**
- Provide user-friendly desktop interface
- Display real-time system status and extracted signals
- Handle system tray integration
- Manage user settings
- Coordinate between UI thread and background processing

**Key Components:**
```python
class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self, app_controller: AppController)
    def setup_ui() -> None
    def update_status(status: dict) -> None
    def show_notification(title: str, message: str) -> None
    def minimize_to_tray() -> None

class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon with context menu"""
    def __init__(self, parent: QWidget)
    def create_menu() -> QMenu
    def update_icon(status: str) -> None  # green/yellow/red/gray
    def show_recent_signals(signals: List[Signal]) -> None

class DashboardWidget(QWidget):
    """Main dashboard showing real-time status"""
    - Connection status indicator
    - Channel list with status
    - Recent signals table (last 20)
    - System metrics (uptime, messages processed, etc.)
    - Error count and last error time

class SignalTableWidget(QTableWidget):
    """Table displaying extracted signals"""
    Columns:
    - Timestamp
    - Channel
    - Symbol
    - Direction
    - Entry
    - SL
    - TP levels
    - Confidence
    - Actions (View details, Copy)

class SettingsDialog(QDialog):
    """Settings configuration dialog"""
    Tabs:
    - Telegram (credentials, session)
    - Channels (add/remove, enable/disable)
    - Extraction (confidence threshold, patterns)
    - Output (file paths, CSV format)
    - GUI (theme, notifications, auto-start)

class ErrorLogViewer(QDialog):
    """View and manage extraction errors"""
    - Display failed messages
    - Retry extraction button
    - Mark as reviewed
    - Export to file

class AppController:
    """Coordinates GUI and background processing"""
    def __init__(self, config: Config)
    def start_monitoring() -> None
    def stop_monitoring() -> None
    def on_new_signal(signal: Signal) -> None  # Callback from extractor
    def on_error(error: ExtractionError) -> None
    def on_connection_status_change(status: str) -> None
```

**Threading Architecture:**
```python
# Main thread: GUI (Qt event loop)
# Worker thread: Telegram client + signal processing

class BackgroundWorker(QThread):
    """Runs Telegram client in background thread"""

    # Signals (Qt signals for thread-safe communication)
    signal_extracted = pyqtSignal(Signal)
    error_occurred = pyqtSignal(ExtractionError)
    status_changed = pyqtSignal(str)

    def run(self):
        # Run asyncio event loop for Telegram client
        asyncio.run(self.monitoring_loop())

    async def monitoring_loop(self):
        # Telegram client operations
        pass
```

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Telegram Signal Extractor              [_] [□] [X]          │
├─────────────────────────────────────────────────────────────┤
│ File  Settings  View  Help                                  │
├─────────────────────────────────────────────────────────────┤
│ Status: ● Connected  │  Uptime: 02:34:15  │  Signals: 47   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌───────────────────────────────────┐ │
│ │ Channels        │  │ Recent Signals                    │ │
│ │                 │  │ ┌────┬──────┬──────┬────┬───────┐ │ │
│ │ ● Nick Alpha    │  │ │Time│Chan..│Symbol│Dir │Entry  │ │ │
│ │ ● Gary Gold     │  │ ├────┼──────┼──────┼────┼───────┤ │ │
│ │                 │  │ │16:3│Nick  │XAUUSD│SELL│4746.50│ │ │
│ │ [+ Add Channel] │  │ │16:2│Gary  │XAUUSD│BUY │4930   │ │ │
│ │                 │  │ │... │...   │...   │... │...    │ │ │
│ │ Metrics         │  │ └────┴──────┴──────┴────┴───────┘ │ │
│ │ Messages: 1,234 │  │                                     │ │
│ │ Extracted: 47   │  │ [View All] [Export] [Clear]        │ │
│ │ Errors: 3       │  └───────────────────────────────────┘ │ │
│ │ Success: 94%    │                                         │ │
│ └─────────────────┘  ┌───────────────────────────────────┐ │
│                      │ Activity Log                       │ │
│                      │ 16:34:12 - New signal extracted    │ │
│                      │ 16:32:05 - Message processed       │ │
│                      │ 16:30:00 - Connection healthy      │ │
│                      └───────────────────────────────────┘ │ │
├─────────────────────────────────────────────────────────────┤
│ Status: Monitoring 2 channels | Last update: 16:34:15      │
└─────────────────────────────────────────────────────────────┘
```

**System Tray Menu:**
```
┌────────────────────────────┐
│ ● Telegram Signal Extractor│
├────────────────────────────┤
│ Show Window                │
│ ───────────────────────    │
│ Recent Signals        ▶    │
│ ───────────────────────    │
│ ✓ Monitoring (Click to stop)│
│ Open Logs Folder           │
│ Open Output CSV            │
│ ───────────────────────    │
│ Settings...                │
│ About...                   │
│ Exit                       │
└────────────────────────────┘
```

## 3. Data Models

### 3.1 Signal Data Structure

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Signal:
    """Represents an extracted trading signal"""

    # Identifiers
    message_id: int
    channel_username: str
    channel_url: str
    timestamp: datetime

    # Trading data
    symbol: str  # e.g., "EURUSD", "GOLD", "BTCUSD"
    direction: str  # "BUY" or "SELL"
    entry_price: Optional[float]
    entry_price_min: Optional[float]  # For range entries
    entry_price_max: Optional[float]  # For range entries
    stop_loss: Optional[float]
    take_profits: List[float]  # [TP1, TP2, TP3, ...]

    # Metadata
    confidence_score: float  # 0.0 to 1.0
    raw_message: str
    extraction_notes: Optional[str]  # Any warnings or notes

    # Processing
    created_at: datetime  # When extraction occurred
    processed: bool = False  # For MT5 EA to mark as processed
```

## 4. API Integration

### 4.1 Telegram API Setup

**Steps to get API credentials:**
1. Visit https://my.telegram.org
2. Log in with phone number
3. Navigate to "API development tools"
4. Create a new application
5. Note down `api_id` and `api_hash`

**Authentication Flow:**
```python
# First run
client = TelegramClient('session_name', api_id, api_hash)
await client.start(phone=phone_number)
# User enters code received via Telegram
# Session is saved to 'session_name.session'

# Subsequent runs
client = TelegramClient('session_name', api_id, api_hash)
await client.start()  # Automatically uses saved session
```

### 4.2 Event Handling

**New Message Handler:**
```python
@client.on(events.NewMessage(chats=['nickalphatrader', 'GaryGoldLegacy']))
async def handler(event):
    message = event.message
    channel = await event.get_chat()

    # Process message
    if signal_extractor.is_signal(message.text):
        signal = signal_extractor.extract_signal(
            message.text,
            metadata={
                'message_id': message.id,
                'channel': channel.username,
                'timestamp': message.date
            }
        )
        csv_writer.write_signal(signal)
```

## 5. Error Handling Strategy

### 5.1 Network Errors
- Implement exponential backoff for reconnection
- Maximum retry attempts: 5
- Log all connection issues
- Send notification after max retries exceeded

### 5.2 Extraction Errors
- Categorize errors:
  - **Partial extraction**: Some fields found, others missing
  - **Ambiguous format**: Multiple interpretations possible
  - **No pattern match**: Message doesn't match any known pattern
- Action: Log original message, continue processing

### 5.3 File I/O Errors
- Handle file lock conflicts (MT5 may be reading CSV)
- Implement retry logic with timeout
- Fallback to queuing signals in memory if file unavailable

## 6. Performance Considerations

### 6.1 Message Processing
- Process messages asynchronously
- Queue-based architecture for high-volume scenarios
- Target: < 5 seconds from message receipt to CSV write

### 6.2 Resource Usage
- Memory: < 100 MB for normal operation
- CPU: Minimal (event-driven, mostly I/O wait)
- Disk: Implement log rotation to prevent unbounded growth

## 7. Security Considerations

### 7.1 Credential Management
- Store API credentials in `.env` file (not in code)
- Add `.env` and `*.session` to `.gitignore`
- Use environment variables in production
- Encrypt session files if storing on shared systems

### 7.2 Data Security
- No logging of sensitive trading information
- Secure file permissions for CSV output (read/write owner only)
- Regular cleanup of old error logs

## 8. Testing Strategy

### 8.1 Unit Tests
- Test extraction patterns with sample messages
- Test CSV writing and file handling
- Test configuration loading

### 8.2 Integration Tests
- Test Telegram connection (with test account)
- Test end-to-end flow with mock channels
- Test error recovery scenarios

### 8.3 Test Data
Create a test message corpus with:
- Valid signals in various formats
- Invalid/ambiguous messages
- Edge cases (missing fields, unusual formatting)

## 9. Deployment

### 9.1 Installation
```bash
# Clone repository
git clone <repo-url>
cd TelegramSignals

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# First run (authentication)
python main.py --setup

# Run
python main.py
```

### 9.2 Running as Service
- **Windows**: Use NSSM (Non-Sucking Service Manager)
- **Linux**: systemd service
- **Docker**: Containerized deployment option

### 9.3 Monitoring
- Health check endpoint (if implementing web interface)
- Heartbeat logs every 5 minutes
- Alert on extraction failure rate > 50%
