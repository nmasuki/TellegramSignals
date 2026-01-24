# System Architecture

## 1. Architecture Overview

The Telegram Signal Extraction System follows a modular, event-driven architecture with a desktop GUI interface, designed for reliability, maintainability, and extensibility.

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           External Systems                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐                          ┌──────────────────┐     │
│  │  Telegram API    │                          │   MT5 Terminal   │     │
│  │  (Cloud)         │                          │   + EA           │     │
│  └────────┬─────────┘                          └─────────▲────────┘     │
│           │                                              │               │
└───────────┼──────────────────────────────────────────────┼───────────────┘
            │                                              │
            │ Events (New Messages)                        │ CSV Read
            ▼                                              │
┌─────────────────────────────────────────────────────────┼───────────────┐
│              Telegram Signal Extractor (Desktop App)    │               │
├─────────────────────────────────────────────────────────┴───────────────┤
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     GUI Layer (Qt/PySide6)                        │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │  │
│  │  │  Main Window │    │ System Tray  │    │ Notification │        │  │
│  │  │  Dashboard   │    │   Icon       │    │   Manager    │        │  │
│  │  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │  │
│  │         │                    │                    │                │  │
│  │         └────────────────────┼────────────────────┘                │  │
│  │                              │                                     │  │
│  │                              ▼                                     │  │
│  │                      ┌───────────────┐                            │  │
│  │                      │  App          │                            │  │
│  │                      │  Controller   │                            │  │
│  │                      └───────┬───────┘                            │  │
│  └──────────────────────────────┼─────────────────────────────────────┘  │
│                                 │                                         │
│                                 │ Qt Signals/Slots                        │
│                                 ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     Application Layer                             │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │  │
│  │  │   Main       │    │   Config     │    │   Logging    │        │  │
│  │  │   Loop       │───▶│   Manager    │    │   Manager    │        │  │
│  │  └──────────────┘    └──────────────┘    └──────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     Application Layer                             │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │  │
│  │  │   Main       │    │   Config     │    │   Logging    │        │  │
│  │  │   Loop       │───▶│   Manager    │    │   Manager    │        │  │
│  │  └──────────────┘    └──────────────┘    └──────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      Business Logic Layer                         │  │
│  │                                                                     │  │
│  │  ┌──────────────────────────────────────────────────────────┐    │  │
│  │  │            Event Handler / Orchestrator                  │    │  │
│  │  │                                                            │    │  │
│  │  │  • Receives new message events                           │    │  │
│  │  │  • Coordinates signal extraction                         │    │  │
│  │  │  • Handles success/failure flows                         │    │  │
│  │  └────────────┬─────────────────────────────┬───────────────┘    │  │
│  │               │                               │                    │  │
│  │               ▼                               ▼                    │  │
│  │  ┌─────────────────────────┐    ┌──────────────────────────┐    │  │
│  │  │   Signal Extractor      │    │   Validation Service     │    │  │
│  │  │                         │    │                          │    │  │
│  │  │  • Pattern matching     │    │  • Data validation       │    │  │
│  │  │  • Text parsing         │───▶│  • Business rules check  │    │  │
│  │  │  • Field extraction     │    │  • Confidence scoring    │    │  │
│  │  └─────────────────────────┘    └──────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      Data Access Layer                            │  │
│  │                                                                     │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │  │
│  │  │  Telegram    │    │     CSV      │    │    Error     │        │  │
│  │  │  Client      │    │   Writer     │    │   Logger     │        │  │
│  │  │  (Telethon)  │    │              │    │              │        │  │
│  │  └──────────────┘    └──────────────┘    └──────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Infrastructure Layer                           │  │
│  │                                                                     │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │  │
│  │  │   Session    │    │   File       │    │   Network    │        │  │
│  │  │   Manager    │    │   System     │    │   Monitor    │        │  │
│  │  └──────────────┘    └──────────────┘    └──────────────┘        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

## 2. Component Details

### 2.1 Application Layer

#### Main Loop
**Responsibility**: Application entry point and lifecycle management

**Key Functions**:
- Initialize all components
- Start Telegram client connection
- Register event handlers
- Handle graceful shutdown

**Flow**:
```python
async def main():
    # 1. Load configuration
    config = ConfigManager.load('config.yaml')

    # 2. Setup logging
    setup_logging(config.logging)

    # 3. Initialize components
    telegram_client = TelegramClient(...)
    signal_extractor = SignalExtractor(config)
    csv_writer = CSVWriter(config.output.csv_file)
    error_logger = ErrorLogger(config.output.error_log)

    # 4. Register event handlers
    event_handler = EventHandler(
        extractor=signal_extractor,
        csv_writer=csv_writer,
        error_logger=error_logger
    )
    telegram_client.add_event_handler(
        event_handler.on_new_message,
        events.NewMessage(chats=config.channels)
    )

    # 5. Connect and run
    await telegram_client.start()
    logger.info("System started, monitoring channels...")

    # 6. Run until interrupted
    await telegram_client.run_until_disconnected()
```

#### Configuration Manager
**Responsibility**: Load, validate, and provide access to configuration

**Features**:
- Load from YAML file
- Override with environment variables
- Validate configuration schema
- Hot-reload support (future)

#### Logging Manager
**Responsibility**: Configure and manage logging infrastructure

**Features**:
- Multiple log outputs (file, console)
- Log rotation
- Structured logging for errors
- Performance metrics logging

### 2.2 Business Logic Layer

#### Event Handler / Orchestrator
**Responsibility**: Coordinate the signal extraction workflow

**Workflow**:
```
New Message Event
      │
      ▼
┌─────────────────┐
│ Is Signal?      │───No──▶ (Ignore, maybe log)
└────────┬────────┘
         │ Yes
         ▼
┌─────────────────┐
│ Extract Signal  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validate Data   │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
  Valid    Invalid
    │          │
    ▼          ▼
┌─────────┐  ┌──────────────┐
│ Write   │  │ Log Error    │
│ to CSV  │  │ Keep Message │
└─────────┘  └──────────────┘
```

**Code Structure**:
```python
class EventHandler:
    def __init__(self, extractor, csv_writer, error_logger):
        self.extractor = extractor
        self.csv_writer = csv_writer
        self.error_logger = error_logger

    async def on_new_message(self, event):
        message = event.message
        channel = await event.get_chat()

        # Check if message is a signal
        if not self.extractor.is_signal(message.text):
            logger.debug(f"Non-signal message from {channel.username}")
            return

        # Extract signal
        try:
            signal = self.extractor.extract_signal(
                message.text,
                metadata={
                    'message_id': message.id,
                    'channel': channel.username,
                    'timestamp': message.date
                }
            )

            # Validate
            if signal.confidence < config.min_confidence:
                raise ExtractionError("Low confidence")

            # Write to CSV
            self.csv_writer.write_signal(signal)
            logger.info(f"Signal extracted: {signal.symbol} {signal.direction}")

        except ExtractionError as e:
            # Log extraction failure
            self.error_logger.log_extraction_error(
                message=message.text,
                channel=channel.username,
                reason=str(e)
            )
            logger.warning(f"Extraction failed: {e}")
```

#### Signal Extractor
**Responsibility**: Parse message text and extract trading signal data

**Architecture**:
```
SignalExtractor
    │
    ├─▶ PatternMatcher (Regex-based)
    │   ├─▶ SymbolPattern
    │   ├─▶ DirectionPattern
    │   ├─▶ EntryPattern
    │   ├─▶ StopLossPattern
    │   └─▶ TakeProfitPattern
    │
    ├─▶ NLPProcessor (Future enhancement)
    │   └─▶ Entity Recognition
    │
    └─▶ ConfidenceScorer
        └─▶ Calculate extraction confidence
```

**Key Methods**:
```python
class SignalExtractor:
    def is_signal(self, text: str) -> bool:
        """Quick check if message contains signal keywords"""
        signal_keywords = ['buy', 'sell', 'entry', 'tp', 'sl', 'stop']
        return any(keyword in text.lower() for keyword in signal_keywords)

    def extract_signal(self, text: str, metadata: dict) -> Signal:
        """Extract complete signal from message"""
        # Extract each field
        symbol = self._extract_symbol(text)
        direction = self._extract_direction(text)
        entry = self._extract_entry(text)
        stop_loss = self._extract_stop_loss(text)
        take_profits = self._extract_take_profits(text)

        # Calculate confidence
        confidence = self._calculate_confidence(
            symbol, direction, entry, stop_loss, take_profits
        )

        # Build signal object
        return Signal(
            message_id=metadata['message_id'],
            channel_username=metadata['channel'],
            timestamp=metadata['timestamp'],
            symbol=symbol,
            direction=direction,
            entry_price=entry.get('single'),
            entry_price_min=entry.get('min'),
            entry_price_max=entry.get('max'),
            stop_loss=stop_loss,
            take_profits=take_profits,
            confidence_score=confidence,
            raw_message=text,
            extracted_at=datetime.now(timezone.utc)
        )
```

#### Validation Service
**Responsibility**: Validate extracted signals against business rules

**Validation Rules**:
1. **Required Fields**: Symbol, direction must be present
2. **Price Validation**: SL and TP prices make sense relative to entry
   - For BUY: SL < Entry < TP
   - For SELL: TP < Entry < SL
3. **Symbol Validation**: Symbol exists in known instruments
4. **Confidence Threshold**: Above minimum configured threshold
5. **Duplicate Detection**: Not a duplicate of recent signal

### 2.3 Data Access Layer

#### Telegram Client (Telethon Wrapper)
**Responsibility**: Interface with Telegram API

**Features**:
- Session management
- Auto-reconnection
- Event subscription
- Rate limiting compliance

**Implementation**:
```python
class TelegramListener:
    def __init__(self, api_id, api_hash, session_file):
        self.client = TelegramClient(session_file, api_id, api_hash)
        self._reconnect_attempts = 0

    async def connect(self):
        """Connect with auto-reconnect logic"""
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                await self._authenticate()
            self._reconnect_attempts = 0
        except Exception as e:
            await self._handle_connection_error(e)

    async def _handle_connection_error(self, error):
        """Exponential backoff reconnection"""
        if self._reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
            delay = 2 ** self._reconnect_attempts
            logger.warning(f"Reconnecting in {delay}s...")
            await asyncio.sleep(delay)
            self._reconnect_attempts += 1
            await self.connect()
        else:
            logger.critical("Max reconnect attempts reached")
            raise
```

#### CSV Writer
**Responsibility**: Write signals to CSV file safely

**Features**:
- Atomic writes (temp file + rename)
- File locking awareness
- Append mode
- Header management

**Implementation**:
```python
class CSVWriter:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def write_signal(self, signal: Signal):
        """Write signal to CSV with file locking"""
        # Convert signal to dict
        row = self._signal_to_dict(signal)

        # Write atomically
        temp_file = self.file_path.with_suffix('.tmp')
        try:
            # Read existing + append
            df = pd.read_csv(self.file_path) if self.file_path.exists() else pd.DataFrame()
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

            # Write to temp
            df.to_csv(temp_file, index=False)

            # Atomic rename
            temp_file.replace(self.file_path)

        except PermissionError:
            # File locked by MT5, retry
            logger.warning("CSV file locked, retrying...")
            time.sleep(0.5)
            self.write_signal(signal)  # Retry once
```

#### Error Logger
**Responsibility**: Log extraction failures and system errors

**Features**:
- Structured JSON logging
- Original message preservation
- Categorized error types
- Searchable logs

### 2.4 Infrastructure Layer

#### Session Manager
**Responsibility**: Manage Telegram session persistence

**Features**:
- Session file storage
- Session validation
- Re-authentication handling

#### File System Manager
**Responsibility**: Handle file operations safely

**Features**:
- Directory creation
- File rotation
- Disk space monitoring
- Atomic operations

#### Network Monitor
**Responsibility**: Monitor network health and connectivity

**Features**:
- Connection health checks
- Latency monitoring
- Automatic recovery triggers

## 3. Data Flow

### 3.1 Normal Flow (Successful Extraction)

```
1. Telegram posts new message
         │
         ▼
2. Telethon client receives event
         │
         ▼
3. EventHandler.on_new_message() called
         │
         ▼
4. SignalExtractor.is_signal() → True
         │
         ▼
5. SignalExtractor.extract_signal()
    │
    ├─▶ Extract symbol
    ├─▶ Extract direction
    ├─▶ Extract entry
    ├─▶ Extract SL
    ├─▶ Extract TPs
    └─▶ Calculate confidence
         │
         ▼
6. ValidationService.validate() → Pass
         │
         ▼
7. CSVWriter.write_signal()
         │
         ▼
8. Signal available in CSV
         │
         ▼
9. MT5 EA reads and processes
```

### 3.2 Error Flow (Extraction Failure)

```
1-4. (Same as normal flow)
         │
         ▼
5. SignalExtractor.extract_signal() → Exception
         │
         ▼
6. EventHandler catches exception
         │
         ▼
7. ErrorLogger.log_extraction_error()
         │
         ▼
8. Error logged to extraction_errors.log
         │
         ▼
9. Processing continues (message skipped)
```

### 3.3 Recovery Flow (Connection Lost)

```
1. Network interruption
         │
         ▼
2. Telethon raises connection error
         │
         ▼
3. TelegramListener.on_disconnect()
         │
         ▼
4. Attempt reconnection (exponential backoff)
    │
    ├─▶ Success → Resume monitoring
    │
    └─▶ Failure → Retry (max 5 attempts)
              │
              └─▶ Max retries → Alert & exit
```

## 4. Deployment Architecture

### 4.1 Single-Server Deployment (Recommended for v1.0)

```
┌─────────────────────────────────────┐
│      Windows Server / Desktop       │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  Telegram Signal Extractor    │ │
│  │  (Running as Windows Service) │ │
│  └───────────┬───────────────────┘ │
│              │                      │
│              ▼                      │
│  ┌───────────────────────────────┐ │
│  │      File System              │ │
│  │  • output/signals.csv         │ │
│  │  • logs/                      │ │
│  │  • sessions/                  │ │
│  └───────────┬───────────────────┘ │
│              │                      │
│              ▼                      │
│  ┌───────────────────────────────┐ │
│  │      MT5 Terminal + EA        │ │
│  │  (Reads signals.csv)          │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 4.2 Future: Distributed Architecture

```
┌──────────────────┐       ┌──────────────────┐
│  Signal Extractor│       │   Web Dashboard  │
│    (Service)     │◀─────▶│   (Monitoring)   │
└────────┬─────────┘       └──────────────────┘
         │
         ▼
┌──────────────────┐
│   Database       │
│   (PostgreSQL)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Multiple MT5   │
│   Instances      │
└──────────────────┘
```

## 5. Security Architecture

### 5.1 Credential Management

```
┌─────────────────┐
│  .env file      │  ← Stored locally, not in version control
│  (Encrypted)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Environment Variables  │  ← Loaded at runtime
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Application Memory     │  ← Used by Telegram client
│  (Runtime only)         │
└─────────────────────────┘
```

### 5.2 Data Protection

- **Session files**: Encrypted, restricted permissions (chmod 600)
- **API credentials**: Environment variables only
- **Logs**: No sensitive data (sanitize before logging)
- **CSV files**: Standard file permissions

## 6. Scalability Considerations

### 6.1 Current Capacity (v1.0)
- **Channels**: 2-10 channels
- **Messages**: ~100-500 per day
- **Response time**: < 5 seconds per message

### 6.2 Scaling Strategy (Future)

**Vertical Scaling** (Single server):
- Increase processing power
- Add memory for caching
- **Limit**: ~50 channels, ~5000 messages/day

**Horizontal Scaling** (Multiple instances):
- Partition channels across instances
- Shared database for signals
- Load balancer for API access
- **Capacity**: 100s of channels, 10,000s of messages/day

## 7. Monitoring and Observability

### 7.1 Health Metrics

```python
class HealthMonitor:
    """Track system health metrics"""

    metrics = {
        'messages_received': 0,
        'signals_extracted': 0,
        'extraction_failures': 0,
        'csv_writes': 0,
        'last_heartbeat': None,
        'connection_status': 'connected',
    }

    def record_metric(self, name, value):
        self.metrics[name] = value

    def get_health_status(self):
        return {
            'status': 'healthy' if self._is_healthy() else 'degraded',
            'metrics': self.metrics,
            'uptime': self._calculate_uptime()
        }
```

### 7.2 Alerting (Future)

```
Trigger Conditions:
- Connection lost > 5 minutes
- Extraction failure rate > 50%
- No signals processed in 24 hours (during trading hours)
- Disk space < 10%
- Memory usage > 90%

Alert Channels:
- Log file (always)
- Email (optional)
- Webhook (Slack, Discord, etc.)
- SMS (critical only)
```

## 8. Error Handling Strategy

### 8.1 Error Categories

| Category | Severity | Action | Example |
|----------|----------|--------|---------|
| Network | High | Auto-retry, alert if persist | Connection timeout |
| Extraction | Low | Log, continue | Unknown signal format |
| File I/O | Medium | Retry, queue in memory | CSV file locked |
| Authentication | Critical | Alert, manual intervention | Session expired |
| System | Critical | Alert, attempt recovery | Out of memory |

### 8.2 Recovery Mechanisms

```python
class ErrorHandler:
    """Centralized error handling"""

    def handle_error(self, error, context):
        category = self._categorize_error(error)

        if category == ErrorCategory.NETWORK:
            return self._handle_network_error(error, context)
        elif category == ErrorCategory.EXTRACTION:
            return self._handle_extraction_error(error, context)
        # ... etc

    def _handle_network_error(self, error, context):
        """Implement exponential backoff retry"""
        for attempt in range(MAX_RETRIES):
            delay = 2 ** attempt
            time.sleep(delay)
            try:
                return context['retry_func']()
            except:
                continue
        raise MaxRetriesExceeded()
```

## 9. Testing Architecture

### 9.1 Test Pyramid

```
         ┌──────────┐
         │   E2E    │  ← Few, critical flows
         │  Tests   │
         └──────────┘
       ┌──────────────┐
       │ Integration  │  ← Component interaction
       │    Tests     │
       └──────────────┘
   ┌────────────────────┐
   │    Unit Tests      │  ← Many, fast, isolated
   └────────────────────┘
```

### 9.2 Test Coverage Targets

- **Unit tests**: 80% code coverage
- **Integration tests**: All critical paths
- **E2E tests**: 2-3 main scenarios

## 10. Future Enhancements

### 10.1 Phase 2 Features
- Web dashboard for monitoring
- Multi-user support
- Advanced signal analytics
- Machine learning for pattern recognition

### 10.2 Phase 3 Features
- Mobile app
- Cloud deployment option
- Real-time signal quality scoring
- Integration with multiple trading platforms
