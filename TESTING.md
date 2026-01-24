# Testing Guide

## Automated Tests

### Run Extraction Tests

Test the signal extraction logic with sample signals:

```bash
# Windows
test_extraction.bat

# Or directly with Python
python tests/test_extraction.py
```

This will test:
- ✅ Pattern matching for both channel formats
- ✅ Symbol extraction and normalization
- ✅ Direction extraction
- ✅ Entry price extraction (single and range)
- ✅ Stop loss extraction
- ✅ Take profit extraction
- ✅ Full signal extraction with confidence scoring
- ✅ Price logic validation (SL/TP relative to entry)
- ✅ CSV output format

**Expected Output:**
```
============================================================
RUNNING ALL TESTS
============================================================

============================================================
TEST: Pattern Matcher
============================================================

--- Nick Alpha Trader Sample 1 ---
Is signal: True
Symbol: XAUUSD
Direction: SELL
Entry: single=None, min=4746.5, max=4750.5
Stop Loss: 4752.5
Take Profits: [(1, 4730.0), (2, 4720.0)]

--- Gary Gold Legacy Sample 1 ---
Is signal: True
Symbol: XAUUSD
Direction: BUY
Entry: single=None, min=4925.0, max=4930.0
Stop Loss: 4922.0
Take Profits: [(1, 4935.0), (2, 4940.0)]

--- Non-Signal Message ---
Is signal: False

✓ Pattern Matcher tests passed!

============================================================
TEST: Signal Extractor
============================================================

--- Extracting Nick Alpha Trader Signal ---
✓ Extraction successful!
  Symbol: XAUUSD
  Direction: SELL
  Entry Range: 4746.5 - 4750.5
  Stop Loss: 4752.5
  Take Profits: [4730.0, 4720.0]
  Confidence: 1.0

--- Extracting Gary Gold Legacy Signal ---
✓ Extraction successful!
  Symbol: XAUUSD
  Direction: BUY
  Entry Range: 4925.0 - 4930.0
  Stop Loss: 4922.0
  Take Profits: [4935.0, 4940.0]
  Confidence: 1.0

✓ Signal Extractor tests passed!

============================================================
✓ ALL TESTS PASSED!
============================================================
```

## Manual Testing

### 1. Test Application Startup

```bash
python src/main.py
```

**Expected:**
- Application connects to Telegram (or prompts for authentication if first run)
- Shows "Monitoring X channel(s)"
- Displays channel list
- Shows "Press Ctrl+C to stop"

**Common Issues:**
- "Config file not found" → Make sure you're in project root
- "Missing telegram.api_id" → Configure `.env` file
- "No channels configured" → Check `config/config.yaml`

### 2. Test First-Time Authentication

**Prerequisites:**
- Valid Telegram API credentials in `.env`
- Delete `sessions/*.session` files to force re-authentication

**Run:**
```bash
python src/main.py
```

**Expected Flow:**
1. "Not authorized, starting authentication..."
2. "Sending code request to +1234567890"
3. Prompt: "Enter the code you received:"
4. Enter 5-digit code from Telegram app
5. "Successfully authenticated!"
6. "Logged in as: [Your Name] (+1234567890)"
7. Application continues to monitor

### 3. Test Session Persistence

**Prerequisites:**
- Successfully authenticated at least once
- Session file exists in `sessions/` folder

**Run:**
```bash
python src/main.py
```

**Expected:**
- "Already authorized, using existing session"
- NO code prompt
- Proceeds directly to monitoring

**Test Passed:** ✅ Session was saved and reused

### 4. Test Channel Access

**Check console output:**
```
Testing channel access...
Successfully accessed channel: @nickalphatrader
Successfully accessed channel: @GaryGoldLegacy
```

**If you see "Cannot access channel":**
- Make sure you've joined the channel in your Telegram app
- Check channel username is correct in config
- Channel may be private (requires manual join)

### 5. Test Signal Extraction (Live)

**Prerequisites:**
- Application running
- Monitoring channels successfully

**Wait for a signal to be posted**, or **send a test message** to a test channel:

**Test Message (Nick Alpha Trader format):**
```
GOLD SELL
Gold sell now @4750-4755
sl: 4757
tp1: 4740
tp2: 4735
```

**Expected Console Output:**
```
2026-01-24 10:30:15 - INFO - Processing potential signal from @testchannel
2026-01-24 10:30:15 - INFO - ✓ Signal extracted and saved: XAUUSD SELL (confidence: 1.00)
```

**Verify:**
1. Check `output/signals.csv` - new row added
2. Open CSV - verify data is correct
3. Check timestamps match

### 6. Test Failed Extraction

**Send a malformed message:**
```
Gold might go down soon around 4750 maybe
```

**Expected:**
```
2026-01-24 10:31:20 - WARNING - ✗ Extraction failed: Confidence score (0.50) below threshold (0.75)
```

**Verify:**
1. Message not in `output/signals.csv`
2. Error logged in `logs/extraction_errors.jsonl`
3. Error log contains the message text and reason

### 7. Test CSV Output Format

**After extracting at least one signal:**

1. Open `output/signals.csv`
2. Check all columns present:
   - message_id, channel_username, timestamp
   - symbol, direction
   - entry_price, entry_price_min, entry_price_max
   - stop_loss
   - take_profit_1, take_profit_2, take_profit_3, take_profit_4
   - confidence_score
   - raw_message, extraction_notes
   - extracted_at

3. Verify data types:
   - Prices are numbers (not text)
   - Timestamps are ISO format
   - Symbol is normalized (XAUUSD, not GOLD)

### 8. Test Graceful Shutdown

**While application is running:**

1. Press `Ctrl+C`
2. Wait for shutdown

**Expected:**
```
Shutdown signal received. Gracefully stopping...
Cleaning up...
Disconnecting from Telegram...
Disconnected from Telegram

============================================================
SESSION STATISTICS
============================================================
Messages processed: 15
Signals extracted: 12
Extraction errors: 3
Success rate: 80.0%
============================================================

Telegram Signal Extractor stopped
```

### 9. Test Configuration Changes

**Edit `config/config.yaml`:**
```yaml
extraction:
  min_confidence: 0.60  # Lower threshold
```

**Restart application**

**Verify:**
- New threshold is used
- More signals pass (if any were previously failing due to low confidence)

### 10. Test Error Logging

**View error log:**
```bash
type logs\extraction_errors.jsonl
```

**Expected format:**
```json
{"message_id": 12345, "channel_username": "testchannel", "timestamp": "2026-01-24T10:31:20", "raw_message": "...", "error_reason": "...", "extracted_fields": {...}, "occurred_at": "2026-01-24T10:31:20"}
```

## Performance Testing

### Test Continuous Operation

**Run for extended period:**
```bash
python src/main.py
```

**Leave running for 1-24 hours**

**Monitor:**
- CPU usage (should be <5% when idle)
- Memory usage (should be ~50-100 MB)
- Check logs for any errors
- Verify signals are still being extracted

**Check after:**
- `output/signals.csv` file size
- `logs/system.log` file size
- No memory leaks (memory stable over time)

### Test High Volume

**Simulate many messages:**
- Join a very active channel
- Monitor for 1 hour

**Verify:**
- All messages processed
- No messages missed
- Performance remains good
- CSV writes successful

## Integration Testing

### Test with MT5 EA (Optional)

1. Ensure `output/signals.csv` has signals
2. Open MT5 terminal
3. Run your EA that reads the CSV
4. Verify EA can read and parse the file
5. Check EA processes signals correctly

**Common CSV Issues:**
- Encoding problems → Check UTF-8 encoding
- Header mismatch → Verify field names match
- File locking → Ensure EA doesn't lock file for writing

## Validation Checklist

Before considering the system production-ready:

### Functionality Tests
- [ ] Application starts without errors
- [ ] Authentication works (first-time)
- [ ] Session persistence works (no re-auth)
- [ ] Channels are accessible
- [ ] Live signal extraction works
- [ ] CSV file created and populated
- [ ] Error logging works
- [ ] Graceful shutdown works

### Accuracy Tests
- [ ] Nick Alpha Trader signals extracted correctly
- [ ] Gary Gold Legacy signals extracted correctly
- [ ] Symbol normalization works (GOLD → XAUUSD)
- [ ] Entry ranges normalized (min/max correct order)
- [ ] Price validation works (SL/TP logic)
- [ ] Confidence scoring reasonable
- [ ] Non-signals ignored

### Reliability Tests
- [ ] Runs for 24 hours without crashing
- [ ] Handles network interruptions (auto-reconnect)
- [ ] Memory usage stable over time
- [ ] No log errors or warnings (normal operation)
- [ ] All signals captured (no data loss)

### Integration Tests
- [ ] CSV format compatible with MT5
- [ ] Error log readable and useful
- [ ] System logs comprehensive
- [ ] Configuration changes apply correctly

## Troubleshooting Tests

### Test: Cannot Connect to Telegram

**Simulate:** Disconnect internet

**Expected:**
- Connection error logged
- Application attempts reconnection
- Shows "Reconnecting..." messages
- After reconnection, continues normally

### Test: Channel Becomes Inaccessible

**Simulate:** Leave a channel in Telegram app

**Expected:**
- Error logged when trying to access channel
- Application continues monitoring other channels
- No crash

### Test: Invalid Signal Format

**Send:** Message with unusual format

**Expected:**
- Extraction attempted
- Failure logged if confidence too low
- Error in `extraction_errors.jsonl`
- Application continues

## Test Results Template

```
TEST RUN: [Date/Time]
======================

Environment:
- OS: Windows 10/11
- Python Version: 3.x.x
- Telethon Version: x.x.x

Tests Performed:
[ ] Automated extraction tests
[ ] First-time authentication
[ ] Session persistence
[ ] Channel access
[ ] Live signal extraction (Nick Alpha)
[ ] Live signal extraction (Gary Gold)
[ ] Failed extraction handling
[ ] CSV output verification
[ ] Graceful shutdown
[ ] 24-hour stability test

Results:
- Signals Extracted: X
- Extraction Errors: Y
- Success Rate: Z%
- Issues Found: [List any issues]

Notes:
[Any observations or issues]

Status: [ ] PASS / [ ] FAIL
```

## Automated Test Coverage

The `tests/test_extraction.py` script covers:

| Test | Coverage |
|------|----------|
| Pattern matching | ✅ Both channel formats |
| Symbol extraction | ✅ With normalization |
| Direction extraction | ✅ Various formats |
| Entry extraction | ✅ Single and range |
| SL/TP extraction | ✅ Multiple TPs |
| Full signal extraction | ✅ End-to-end |
| Confidence scoring | ✅ Calculated correctly |
| Price validation | ✅ BUY and SELL logic |
| CSV output | ✅ Format verification |

**Not covered by automated tests:**
- Telegram authentication
- Network resilience
- Session persistence
- Live channel access
- MT5 integration

These require manual testing or integration tests.

## Next: Start Testing!

1. **Run automated tests:** `python tests/test_extraction.py`
2. **Test application startup:** `python src/main.py`
3. **Wait for live signals** or use test channel
4. **Verify CSV output** looks correct
5. **Check error logging** works
6. **Test for 24 hours** to ensure stability

Good luck! 🧪
