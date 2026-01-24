# Data Format Specification

## 1. CSV Output Format

### 1.1 File Specification

**File Name**: `signals.csv`
**Location**: `output/signals.csv` (configurable)
**Encoding**: UTF-8
**Line Ending**: Windows (CRLF) for MT5 compatibility
**Delimiter**: Comma (`,`)
**Quote Character**: Double quote (`"`)

### 1.2 CSV Schema

| Column Name | Data Type | Format | Required | Description | Example |
|------------|-----------|--------|----------|-------------|---------|
| message_id | Integer | Plain number | Yes | Unique Telegram message ID | 12345 |
| channel | String | Plain text | Yes | Channel username | nickalphatrader |
| timestamp | DateTime | ISO 8601 | Yes | When message was posted | 2026-01-24T10:30:00Z |
| symbol | String | Uppercase | Yes | Trading symbol/pair | EURUSD |
| direction | String | BUY or SELL | Yes | Trade direction | BUY |
| entry_price | Float | Decimal | No | Single entry price | 1.0850 |
| entry_min | Float | Decimal | No | Minimum entry (range) | 1.0850 |
| entry_max | Float | Decimal | No | Maximum entry (range) | 1.0900 |
| stop_loss | Float | Decimal | No | Stop loss level | 1.0800 |
| tp1 | Float | Decimal | No | Take profit level 1 | 1.0950 |
| tp2 | Float | Decimal | No | Take profit level 2 | 1.1000 |
| tp3 | Float | Decimal | No | Take profit level 3 | 1.1050 |
| tp4 | Float | Decimal | No | Take profit level 4 | 1.1100 |
| confidence | Float | 0.0 - 1.0 | Yes | Extraction confidence score | 0.95 |
| extracted_at | DateTime | ISO 8601 | Yes | When extraction occurred | 2026-01-24T10:30:05Z |
| processed | Boolean | 0 or 1 | Yes | MT5 EA processing flag | 0 |
| notes | String | Plain text | No | Extraction warnings/notes | "Partial: TP3 missing" |

### 1.3 Sample CSV Content

```csv
message_id,channel,timestamp,symbol,direction,entry_price,entry_min,entry_max,stop_loss,tp1,tp2,tp3,tp4,confidence,extracted_at,processed,notes
12345,nickalphatrader,2026-01-24T10:30:00Z,EURUSD,BUY,1.0850,,,1.0800,1.0950,1.1000,1.1050,,0.95,2026-01-24T10:30:05Z,0,
12346,GaryGoldLegacy,2026-01-24T11:15:00Z,XAUUSD,SELL,,2045.00,2050.00,2060.00,2035.00,2025.00,2015.00,2005.00,0.92,2026-01-24T11:15:03Z,0,"Range entry detected"
12347,nickalphatrader,2026-01-24T12:00:00Z,GBPJPY,BUY,185.50,,,185.00,186.50,187.50,,,0.88,2026-01-24T12:00:02Z,0,"TP3 not found"
```

### 1.4 Field Population Rules

#### Entry Price Fields
- **Single Entry**: Populate `entry_price`, leave `entry_min` and `entry_max` empty
- **Range Entry**: Populate `entry_min` and `entry_max`, leave `entry_price` empty
- If both formats detected: Prefer range entry

#### Take Profit Fields
- Populate TP1, TP2, TP3, TP4 in order as found
- If only one TP: Use TP1
- If more than 4 TPs: Use first 4, note in `notes` field
- Empty fields: Leave blank (not 0)

#### Confidence Score
- 1.0: All required fields extracted with high certainty
- 0.8-0.9: All fields found, some minor ambiguity
- 0.6-0.7: Partial extraction or significant ambiguity
- < 0.6: Low confidence, manual review recommended

## 2. Symbol Normalization

### 2.1 Forex Pairs

**Input Variations** → **Normalized Output**

| Input | Output | Notes |
|-------|--------|-------|
| EUR/USD | EURUSD | Remove slashes |
| EURUSD | EURUSD | Already normalized |
| EUR-USD | EURUSD | Remove dashes |
| eurusd | EURUSD | Uppercase |
| Euro Dollar | EURUSD | Keyword mapping |

### 2.2 Common Symbol Mappings

```python
SYMBOL_ALIASES = {
    # Forex
    "EUR/USD": "EURUSD",
    "GBP/USD": "GBPUSD",
    "USD/JPY": "USDJPY",
    "EUR/GBP": "EURGBP",

    # Metals
    "GOLD": "XAUUSD",
    "XAU/USD": "XAUUSD",
    "XAU": "XAUUSD",
    "SILVER": "XAGUSD",
    "XAG/USD": "XAGUSD",

    # Indices
    "US30": "US30",
    "NAS100": "NAS100",
    "SPX500": "SPX500",
    "DJ30": "US30",
    "NASDAQ": "NAS100",

    # Crypto
    "BTC/USD": "BTCUSD",
    "BITCOIN": "BTCUSD",
    "ETH/USD": "ETHUSD",
    "ETHEREUM": "ETHUSD",
}
```

### 2.3 Symbol Validation

Maintain a whitelist of valid symbols per broker:
- Verify extracted symbol against broker's instrument list
- Flag unknown symbols in `notes` field
- Consider broker-specific symbol formats (e.g., XAUUSD vs GOLD)

## 3. Error Log Format

### 3.1 File Specification

**File Name**: `extraction_errors.log`
**Location**: `logs/extraction_errors.log`
**Format**: JSON Lines (JSONL) - one JSON object per line

### 3.2 Error Log Schema

```json
{
  "timestamp": "2026-01-24T10:30:00Z",
  "channel": "nickalphatrader",
  "message_id": 12348,
  "error_type": "NO_PATTERN_MATCH",
  "confidence": 0.0,
  "raw_message": "🔥 Great trading day everyone! Remember to manage your risk!",
  "extraction_attempts": {
    "symbol": null,
    "direction": null,
    "entry": null,
    "stop_loss": null,
    "take_profits": []
  },
  "reason": "No trading signal detected in message",
  "retry_count": 0
}
```

### 3.3 Error Types

| Error Code | Description | Action Required |
|------------|-------------|-----------------|
| NO_PATTERN_MATCH | No signal pattern found | Review message; may not be a signal |
| AMBIGUOUS_SYMBOL | Multiple symbols detected | Add disambiguation rules |
| AMBIGUOUS_DIRECTION | Cannot determine BUY/SELL | Improve direction extraction |
| MISSING_REQUIRED_FIELD | SL, TP, or Entry missing | Review if partial signal acceptable |
| INVALID_PRICE_FORMAT | Cannot parse price value | Check number format patterns |
| CONFIDENCE_TOO_LOW | Extraction below threshold | Manual review recommended |

## 4. System Log Format

### 4.1 File Specification

**File Name**: `system.log`
**Location**: `logs/system.log`
**Format**: Standard logging format

### 4.2 Log Entry Format

```
2026-01-24 10:30:00,123 - INFO - TelegramListener - Connected to Telegram
2026-01-24 10:30:05,456 - INFO - TelegramListener - Monitoring channels: ['nickalphatrader', 'GaryGoldLegacy']
2026-01-24 10:30:15,789 - INFO - SignalExtractor - New message received from nickalphatrader
2026-01-24 10:30:16,012 - INFO - SignalExtractor - Signal extracted: EURUSD BUY @ 1.0850
2026-01-24 10:30:16,234 - INFO - CSVWriter - Signal written to CSV (ID: 12345)
2026-01-24 10:35:00,567 - WARNING - SignalExtractor - Partial extraction: TP3 missing (message_id: 12347)
2026-01-24 10:40:00,890 - ERROR - TelegramListener - Connection lost, attempting reconnect...
2026-01-24 10:40:05,123 - INFO - TelegramListener - Reconnected successfully
```

### 4.3 Log Levels

- **DEBUG**: Detailed extraction steps, pattern matches
- **INFO**: Normal operations, successful extractions
- **WARNING**: Partial extractions, minor issues
- **ERROR**: Connection failures, file I/O errors
- **CRITICAL**: System crashes, unrecoverable errors

## 5. Configuration File Format

### 5.1 config.yaml Structure

```yaml
telegram:
  api_id: 12345678
  api_hash: "your_api_hash_here"
  phone: "+1234567890"
  session_file: "sessions/telegram.session"

channels:
  - url: "https://t.me/nickalphatrader"
    username: "nickalphatrader"
    enabled: true
    custom_patterns: []  # Channel-specific extraction rules

  - url: "https://t.me/GaryGoldLegacy"
    username: "GaryGoldLegacy"
    enabled: true
    custom_patterns: []

output:
  csv_file: "output/signals.csv"
  error_log: "logs/extraction_errors.log"
  system_log: "logs/system.log"

  # CSV options
  include_header: true
  append_mode: true

  # File rotation
  max_file_size_mb: 50
  keep_backups: 5

extraction:
  # Confidence threshold (0.0 - 1.0)
  min_confidence: 0.6

  # Field requirements
  require_entry: true
  require_stop_loss: false
  require_take_profit: false

  # Behavior
  allow_partial_extraction: true
  skip_duplicates: true
  duplicate_window_minutes: 30

monitoring:
  heartbeat_interval_seconds: 300
  max_reconnect_attempts: 5
  reconnect_delay_seconds: 30

  # Health checks
  check_csv_writable: true
  alert_on_extraction_failure_rate: 0.5

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
  rotation: "daily"
  retention_days: 30
```

### 5.2 Environment Variables (.env)

```bash
# Telegram API Credentials
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+1234567890

# Optional: Database (future enhancement)
# DATABASE_URL=postgresql://user:pass@localhost/signals

# Optional: Notification endpoints
# ALERT_WEBHOOK_URL=https://hooks.slack.com/...
# ALERT_EMAIL=trader@example.com
```

## 6. MT5 Integration Specification

### 6.1 CSV Reading Guidelines for MT5 EA

**File Access**:
- Open CSV in read-only mode
- Implement file lock detection and retry
- Read only new (unprocessed) rows

**Processing Flow**:
```mql5
// Pseudo-code for MT5 EA
int file = FileOpen("signals.csv", FILE_READ|FILE_CSV);
while (!FileIsEnding(file)) {
    string row[] = FileReadLine(file);
    if (row[14] == "0") {  // processed column
        ProcessSignal(row);
        MarkAsProcessed(row[0]);  // message_id
    }
}
FileClose(file);
```

**Marking as Processed**:
- Option 1: EA updates `processed` column to `1`
- Option 2: EA copies row to `processed_signals.csv` and deletes from main file
- **Recommendation**: Option 2 to avoid concurrent write issues

### 6.2 Data Type Mapping

| CSV Column | MT5 Data Type | Conversion Notes |
|------------|---------------|------------------|
| symbol | string | Map to broker symbol if different |
| direction | ENUM_ORDER_TYPE | "BUY" → ORDER_TYPE_BUY |
| entry_price | double | Direct conversion |
| stop_loss | double | Direct conversion |
| tp1-tp4 | double | Handle NULL/empty as 0.0 |
| timestamp | datetime | Parse ISO 8601 to MQL datetime |

## 7. Example Message Formats and Expected Output

### 7.1 Format 1: Standard Format

**Input Message:**
```
🔥 EURUSD SIGNAL

BUY @ 1.0850
SL: 1.0800
TP1: 1.0950
TP2: 1.1000
TP3: 1.1050
```

**Expected CSV Row:**
```csv
12345,nickalphatrader,2026-01-24T10:30:00Z,EURUSD,BUY,1.0850,,,1.0800,1.0950,1.1000,1.1050,,0.98,2026-01-24T10:30:05Z,0,
```

### 7.2 Format 2: Range Entry

**Input Message:**
```
GOLD SELL SETUP

Entry Zone: 2045 - 2050
Stop: 2060
Targets: 2035, 2025, 2015
```

**Expected CSV Row:**
```csv
12346,GaryGoldLegacy,2026-01-24T11:00:00Z,XAUUSD,SELL,,2045.00,2050.00,2060.00,2035.00,2025.00,2015.00,,0.92,2026-01-24T11:00:03Z,0,"Range entry"
```

### 7.3 Format 3: Minimal Format

**Input Message:**
```
GBP/JPY BUY 185.50
Stop 185.00
Target 186.50
```

**Expected CSV Row:**
```csv
12347,nickalphatrader,2026-01-24T12:00:00Z,GBPJPY,BUY,185.50,,,185.00,186.50,,,,0.85,2026-01-24T12:00:02Z,0,"Single TP"
```

### 7.4 Format 4: Non-Signal Message

**Input Message:**
```
Good morning traders!
Remember to check your risk management before taking any trades today.
```

**Expected Output:**
- No CSV entry
- Error log entry with error_type: "NO_PATTERN_MATCH"
