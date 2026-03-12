#!/usr/bin/env python
"""
Test script for signal extraction pipeline.

Simulates receiving a Telegram message by passing command line arguments
through the same extraction pipeline used for real messages.

Usage:
    python scripts/test_signal.py "GOLD BUY" "Entry: 2650" "SL: 2640" "TP: 2670"
    python scripts/test_signal.py "XAUUSD SELL @ 2655" "Stop Loss 2665" "Take Profit 2640"

Each argument becomes a line in the message (joined with newlines).
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.extraction.extractor import SignalExtractor
from src.storage.csv_writer import CSVWriter
from src.storage.error_logger import ErrorLogger
from src.server.signal_store import SignalStore


def print_separator(char="-", length=60):
    print(char * length)


def print_signal(signal):
    """Print signal details in a formatted way"""
    print_separator("=")
    print("EXTRACTED SIGNAL")
    print_separator("=")
    print(f"  Symbol:      {signal.symbol}")
    print(f"  Direction:   {signal.direction}")
    print(f"  Entry:       {signal.entry_price or f'{signal.entry_price_min} - {signal.entry_price_max}'}")
    print(f"  Stop Loss:   {signal.stop_loss}")
    print(f"  Take Profits: {signal.take_profits}")
    print(f"  Confidence:  {signal.confidence_score:.2%}")
    print(f"  Channel:     @{signal.channel_username}")
    print(f"  Message ID:  {signal.message_id}")
    print(f"  Timestamp:   {signal.timestamp}")
    print_separator("=")


def main():
    parser = argparse.ArgumentParser(
        description="Test signal extraction pipeline with simulated messages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "GOLD BUY" "Entry: 2650" "SL: 2640" "TP: 2670"
  %(prog)s "XAUUSD SELL @ 2655" "Stop Loss 2665" "Take Profit 2640"
  %(prog)s --channel TestChannel "BTC BUY 95000" "SL 94000" "TP1 96000" "TP2 97000"
  %(prog)s --no-save "EURUSD BUY 1.0850" "SL 1.0800" "TP 1.0950"
"""
    )

    parser.add_argument(
        "lines",
        nargs="+",
        help="Message lines (each argument becomes a line in the message)"
    )
    parser.add_argument(
        "--channel", "-c",
        default="TestChannel",
        help="Simulated channel username (default: TestChannel)"
    )
    parser.add_argument(
        "--message-id", "-m",
        type=int,
        default=None,
        help="Message ID (default: auto-generated from timestamp)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save to CSV or signal store (dry run)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output including raw extraction data"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.yaml file"
    )

    args = parser.parse_args()

    # Join arguments with newlines to create the message
    message_text = "\n".join(args.lines)

    # Generate message ID if not provided
    message_id = args.message_id or int(datetime.now().timestamp() * 1000) % 1000000
    timestamp = datetime.now()
    channel_username = args.channel

    print_separator("=")
    print("TEST SIGNAL EXTRACTION")
    print_separator("=")
    print(f"Channel: @{channel_username}")
    print(f"Message ID: {message_id}")
    print(f"Timestamp: {timestamp}")
    print_separator("-")
    print("MESSAGE:")
    print_separator("-")
    print(message_text)
    print_separator("-")
    print()

    # Initialize config
    try:
        config = ConfigManager(config_path=args.config, validate=False)
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        print("Using default extraction settings...")
        # Create minimal config for extraction
        config = type('Config', (), {
            'get_extraction_config': lambda self: {
                'min_confidence': 0.5,  # Lower threshold for testing
                'symbol_mapping': {
                    'GOLD': 'XAUUSD', 'Gold': 'XAUUSD', 'XAU/USD': 'XAUUSD',
                    'EUR/USD': 'EURUSD', 'GBP/USD': 'GBPUSD', 'BTC/USD': 'BTCUSD',
                },
                'channel_confidence': {channel_username: 1.0}
            },
            'get_csv_path': lambda self: project_root / 'output' / 'signals.csv',
            'get_error_log_path': lambda self: project_root / 'logs' / 'extraction_errors.jsonl',
            'project_root': project_root
        })()

    # Initialize extractor
    extraction_config = config.get_extraction_config()
    extraction_config['channel_confidence'] = {channel_username: 1.0}  # Full confidence for test channel

    extractor = SignalExtractor(extraction_config)

    # Check if it looks like a signal
    is_signal = extractor.is_signal(message_text)
    print(f"Is Signal: {is_signal}")

    if not is_signal:
        print("\n[WARN]  Message does not appear to contain a trading signal.")
        print("    (No signal keywords detected)")
        return 1

    # Try to extract signal
    try:
        signal = extractor.extract_signal(
            message_text,
            message_id,
            channel_username,
            timestamp
        )

        print_signal(signal)

        # Save to CSV and signal store (unless --no-save)
        if not args.no_save:
            print("\nSaving signal...")

            # CSV Writer
            csv_path = config.get_csv_path()
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            csv_writer = CSVWriter(csv_path)
            csv_writer.write_signal(signal)
            print(f"  [OK] Saved to CSV: {csv_path}")

            # Signal Store (for MT5 EA)
            store_path = config.project_root / 'data' / 'signal_store.json'
            store_path.parent.mkdir(parents=True, exist_ok=True)
            signal_store = SignalStore(persistence_path=str(store_path))
            if signal_store.add_signal(signal):
                print(f"  [OK] Added to signal store: {store_path}")
            else:
                print(f"  ⚠ Signal may be duplicate (already in store)")
        else:
            print("\n(Dry run - signal not saved)")

        print("\n[OK] Signal extraction successful!")
        return 0

    except ValueError as e:
        print(f"\n[WARN]  Extraction failed: {e}")

        if args.verbose:
            # Show what was extracted for debugging
            print("\nPartial extraction results:")
            print(f"  Symbol: {extractor.pattern_matcher.extract_symbol(message_text)}")
            print(f"  Direction: {extractor.pattern_matcher.extract_direction(message_text)}")
            entry = extractor.pattern_matcher.extract_entry(message_text)
            print(f"  Entry: {entry}")
            print(f"  Stop Loss: {extractor.pattern_matcher.extract_stop_loss(message_text)}")
            print(f"  Take Profits: {extractor.pattern_matcher.extract_take_profits(message_text)}")

        return 1

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
