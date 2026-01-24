# Telegram Signal Extractor

Automated system for extracting trading signals from Telegram channels and saving them to CSV for MT5 EA processing.

## Features

- ✅ Real-time monitoring of Telegram channels
- ✅ Automated signal extraction using pattern matching
- ✅ Support for Nick Alpha Trader and Gary Gold Legacy formats
- ✅ CSV output compatible with MT5 Expert Advisors
- ✅ Error logging for failed extractions
- ✅ Confidence scoring for extraction quality
- ✅ Price validation (SL/TP logic checking)

## Quick Start

### 1. Prerequisites

- Python 3.9 or higher
- Telegram account with API credentials
- Access to target Telegram channels

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

1. **Get Telegram API Credentials**:
   - Visit https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Note your `API ID` and `API Hash`

2. **Create `.env` file**:
   ```bash
   cp config/.env.example .env
   ```

3. **Edit `.env` with your credentials**:
   ```
   TELEGRAM_API_ID=38958887
   TELEGRAM_API_HASH=your_api_hash_here
   TELEGRAM_PHONE=+1234567890
   ```

4. **Configure channels** in `config/config.yaml`:
   ```yaml
   channels:
     - username: "nickalphatrader"
       enabled: true
     - username: "GaryGoldLegacy"
       enabled: true
   ```

### 4. First Run (Authentication)

On first run, you'll need to authenticate with Telegram:

```bash
python src/main.py
```

You'll be prompted to:
1. Confirm your phone number
2. Enter the verification code sent to your Telegram app

After first authentication, the session is saved and you won't need to re-authenticate.

### 5. Running the Application

```bash
python src/main.py
```

The application will:
- Connect to Telegram
- Monitor configured channels
- Extract signals automatically
- Save them to `output/signals.csv`
- Log errors to `logs/extraction_errors.jsonl`

Press `Ctrl+C` to stop gracefully.

## Output Format

### signals.csv

The extracted signals are saved in CSV format with these columns:

| Column | Description |
|--------|-------------|
| message_id | Telegram message ID |
| channel_username | Source channel |
| timestamp | Message timestamp |
| symbol | Trading symbol (e.g., XAUUSD) |
| direction | BUY or SELL |
| entry_price | Single entry price (if applicable) |
| entry_price_min | Entry range minimum |
| entry_price_max | Entry range maximum |
| stop_loss | Stop loss level |
| take_profit_1 | First take profit |
| take_profit_2 | Second take profit |
| take_profit_3 | Third take profit |
| take_profit_4 | Fourth take profit |
| confidence_score | Extraction confidence (0.0-1.0) |
| raw_message | Original message text |
| extraction_notes | Any warnings or notes |
| extracted_at | Extraction timestamp |

### extraction_errors.jsonl

Failed extractions are logged in JSONL format for manual review.

## Configuration

### config.yaml

Main configuration file:

```yaml
extraction:
  min_confidence: 0.75  # Minimum confidence threshold

channels:
  - username: "nickalphatrader"
    enabled: true

output:
  csv:
    file_path: "output/signals.csv"
  error_log:
    file_path: "logs/extraction_errors.jsonl"

logging:
  level: INFO
```

### Environment Variables

Override configuration with environment variables:

- `TELEGRAM_API_ID` - Telegram API ID
- `TELEGRAM_API_HASH` - Telegram API Hash
- `TELEGRAM_PHONE` - Phone number for authentication
- `MIN_CONFIDENCE` - Minimum confidence threshold
- `CSV_OUTPUT_PATH` - CSV output path
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Supported Signal Formats

### Nick Alpha Trader

```
GOLD SELL
Gold sell now @4746.50-4750.50
sl: 4752.50
tp1: 4730
tp2: 4720
```

### Gary Gold Legacy

```
GARY GOLD LEGACY
Gold Buy Now @ 4930-4925
sl:4922
tp1:4935
tp2:4940
```

Both formats are automatically detected and processed.

## Troubleshooting

### Authentication Issues

If you get authentication errors:
1. Check that your API credentials are correct
2. Make sure your phone number includes country code (e.g., +1234567890)
3. Delete `sessions/*.session` files and re-authenticate

### Cannot Access Channel

If the app can't access a channel:
1. Make sure you've joined the channel in your Telegram app
2. Check that the channel username is correct (without @)
3. Some channels may require manual join before monitoring

### Low Extraction Success Rate

If many signals are failing extraction:
1. Check `logs/extraction_errors.jsonl` to see failure reasons
2. Adjust `min_confidence` threshold in config
3. The signal format may have changed - check documentation

## Logs

- `logs/system.log` - Application logs
- `logs/extraction_errors.jsonl` - Failed extraction attempts

## MT5 Integration

The CSV file can be read by MT5 Expert Advisors. Example MQL5 code:

```mql5
// Read signals.csv and process unprocessed signals
// Implementation depends on your EA logic
```

See `docs/data-format.md` for detailed CSV schema documentation.

## Documentation

Full documentation is available in the `docs/` folder:

- [Requirements](docs/requirements.md)
- [Technical Specifications](docs/technical-specifications.md)
- [Architecture](docs/architecture.md)
- [Signal Formats](docs/signal-formats.md)
- [Data Format](docs/data-format.md)
- [Implementation Roadmap](docs/implementation-roadmap.md)

## Project Structure

```
TellegramSignals/
├── config/               # Configuration files
│   ├── config.yaml      # Main configuration
│   └── .env.example     # Environment template
├── docs/                # Documentation
├── src/                 # Source code
│   ├── config/         # Configuration management
│   ├── telegram/       # Telegram client wrapper
│   ├── extraction/     # Signal extraction engine
│   ├── storage/        # CSV writer & error logger
│   ├── utils/          # Utilities
│   └── main.py         # Application entry point
├── tests/              # Test suite
├── output/             # CSV output files
├── logs/               # Log files
├── sessions/           # Telegram session files
└── requirements.txt    # Python dependencies
```

## License

[To be determined]

## Support

For issues or questions, check the documentation in the `docs/` folder or review the logs.

## Development Status

**Current**: Phase 4 Complete - Console Application
**Next**: Phase 6 - Desktop GUI (optional)

The console application is fully functional. A desktop GUI with system tray integration is planned for Phase 6.
