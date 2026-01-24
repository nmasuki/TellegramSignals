# Telegram Signal Extraction System - Requirements Document

## Project Overview
A system that monitors Telegram channels for trading signals, extracts structured data from messages, and saves them to CSV files for consumption by MT5 Expert Advisors.

## 1. Functional Requirements

### 1.1 Channel Monitoring
- **FR-1.1**: System shall continuously monitor specified Telegram channels for new messages
- **FR-1.2**: Initial target channels:
  - https://t.me/nickalphatrader
  - https://t.me/GaryGoldLegacy
- **FR-1.3**: System shall support adding additional channels without code modification
- **FR-1.4**: System shall track the last processed message to avoid duplicate processing

### 1.2 Signal Extraction
- **FR-2.1**: System shall extract the following fields from trade signal messages:
  - Trading symbol/pair (e.g., EURUSD, GOLD, BTCUSD)
  - Trade direction (BUY/SELL)
  - Entry price
  - Stop Loss (SL) level
  - Take Profit (TP) levels (support multiple TP targets)
  - Timestamp of the message
  - Source channel identifier
- **FR-2.2**: System shall use pattern matching/NLP to identify signals in various message formats
- **FR-2.3**: System shall handle common variations in signal formatting:
  - Different currency pair notations (EUR/USD, EURUSD, EUR-USD)
  - Multiple TP levels (TP1, TP2, TP3)
  - Range entries (Entry: 1.0850-1.0900)
  - Abbreviated terms (e.g., "SL", "Stop", "StopLoss")

### 1.3 Data Storage
- **FR-3.1**: System shall save extracted signals to CSV file format
- **FR-3.2**: CSV file shall be readable by MT5 Expert Advisors
- **FR-3.3**: System shall append new signals to existing CSV file
- **FR-3.4**: System shall maintain a separate error log for messages that failed extraction

### 1.4 Authentication
- **FR-4.1**: System shall authenticate with Telegram using phone number + verification code
- **FR-4.2**: System shall save session data to avoid repeated authentication
- **FR-4.3**: System shall handle session expiration and prompt for re-authentication

### 1.5 Error Handling
- **FR-5.1**: When signal extraction fails or is ambiguous, system shall:
  - Log the original message to error log file
  - Include channel name, timestamp, and reason for failure
  - Continue processing subsequent messages
- **FR-5.2**: System shall gracefully handle network interruptions and reconnect automatically
- **FR-5.3**: System shall validate extracted data before writing to CSV

### 1.6 User Interface (Desktop Application)
- **FR-6.1**: System shall provide a desktop GUI application for Windows
- **FR-6.2**: Application shall display real-time status dashboard showing:
  - Connection status to Telegram
  - List of monitored channels and their status
  - Recent signals extracted (last 10-20)
  - System metrics (messages processed, signals extracted, errors)
  - Current system health
- **FR-6.3**: Application shall minimize to system tray when closed
- **FR-6.4**: Application shall display system tray icon with status indicator:
  - Green: Connected and running
  - Yellow: Warning (connection issues, high error rate)
  - Red: Critical error or disconnected
  - Gray: Stopped
- **FR-6.5**: System tray icon shall provide context menu with:
  - Show/Hide application window
  - Start/Stop monitoring
  - View recent signals
  - Open logs folder
  - Exit application
- **FR-6.6**: Application shall start automatically with Windows (optional setting)
- **FR-6.7**: Application shall provide notifications for:
  - New signals extracted
  - Connection errors
  - Authentication required
- **FR-6.8**: Application shall provide settings panel for:
  - Adding/removing channels
  - Adjusting extraction confidence threshold
  - Configuring notification preferences
  - Setting output file paths
- **FR-6.9**: Application shall display extraction error log with ability to:
  - View failed messages
  - Retry extraction manually
  - Mark as reviewed
- **FR-6.10**: Application shall remain running in background when minimized to tray

## 2. Non-Functional Requirements

### 2.1 Performance
- **NFR-1.1**: System shall process new messages within 5 seconds of receipt
- **NFR-1.2**: System shall handle multiple channels concurrently
- **NFR-1.3**: System shall maintain operation 24/7 with minimal resource usage

### 2.2 Reliability
- **NFR-2.1**: System uptime target: 99.5%
- **NFR-2.2**: No signal loss due to system errors
- **NFR-2.3**: Automatic recovery from connection failures

### 2.3 Maintainability
- **NFR-3.1**: Configuration shall be externalized (config file for channels, API keys, etc.)
- **NFR-3.2**: Logging shall be comprehensive for troubleshooting
- **NFR-3.3**: Code shall be modular to allow easy updates to extraction patterns

### 2.4 Security
- **NFR-4.1**: Telegram credentials shall be stored securely (encrypted or environment variables)
- **NFR-4.2**: Session files shall have restricted file permissions
- **NFR-4.3**: No sensitive data shall be logged in plain text

### 2.5 Usability
- **NFR-5.1**: Application shall have intuitive, clean user interface
- **NFR-5.2**: Application startup time shall be less than 5 seconds
- **NFR-5.3**: UI shall remain responsive during background operations
- **NFR-5.4**: System tray icon shall be clearly visible on light and dark system themes
- **NFR-5.5**: Notifications shall be non-intrusive and dismissible
- **NFR-5.6**: Application shall remember window size and position

### 2.6 Platform
- **NFR-6.1**: Application shall run on Windows 10 and Windows 11
- **NFR-6.2**: Application shall have single executable deployment option
- **NFR-6.3**: Application shall work on both 64-bit and 32-bit Windows (64-bit preferred)

## 3. User Stories

### US-1: Initial Setup
**As a** trader
**I want to** configure the system with my Telegram credentials and target channels
**So that** I can start receiving automated signal extraction

### US-2: Real-time Signal Processing
**As a** trader
**I want** signals to be extracted and saved to CSV automatically as they're posted
**So that** my MT5 EA can execute trades with minimal delay

### US-3: Review Failed Extractions
**As a** trader
**I want to** review messages that failed extraction in an error log
**So that** I can manually process them or improve the extraction rules

### US-4: Monitor System Health
**As a** trader
**I want to** see logs indicating system status and activity
**So that** I can ensure the system is running correctly

### US-5: View Dashboard
**As a** trader
**I want to** see a real-time dashboard showing extracted signals and system status
**So that** I can monitor activity without checking CSV files or logs

### US-6: Run in Background
**As a** trader
**I want the** application to run in the system tray
**So that** it doesn't clutter my taskbar while still being easily accessible

### US-7: Receive Notifications
**As a** trader
**I want to** receive desktop notifications when new signals are extracted
**So that** I'm aware of new trading opportunities immediately

### US-8: Quick Access
**As a** trader
**I want to** right-click the tray icon to quickly view recent signals
**So that** I can check latest signals without opening the full application

## 4. Constraints

- **C-1**: Must comply with Telegram API terms of service
- **C-2**: Must not perform automated actions that could trigger Telegram rate limits
- **C-3**: CSV output format must be compatible with MT5 file reading capabilities
- **C-4**: System must run on Windows (for MT5 compatibility)

## 5. Assumptions

- **A-1**: User has a valid Telegram account with access to target channels
- **A-2**: Target channels post signals in text format (not images)
- **A-3**: Signal format within each channel is relatively consistent
- **A-4**: MT5 EA will handle CSV file locking/reading appropriately
- **A-5**: Sufficient network connectivity for continuous Telegram connection

## 6. Future Enhancements (Out of Scope for v1.0)

- Web dashboard for monitoring
- Support for image-based signals (OCR)
- Backtesting signal accuracy
- Multi-language signal support
- Integration with multiple brokers beyond MT5
- Signal filtering based on risk parameters
- Automated signal validation against market conditions
