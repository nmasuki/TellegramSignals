"""Fetch historical messages from the last 24 hours and extract signals"""
import asyncio
import sys
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from telethon import TelegramClient
from dotenv import load_dotenv
import yaml

from src.extraction.extractor import SignalExtractor
from src.storage.csv_writer import CSVWriter


def safe_print(text):
    """Print text safely, replacing problematic characters"""
    try:
        # Remove emojis for console display
        clean_text = re.sub(r'[\U00010000-\U0010ffff]', '', str(text))
        print(clean_text)
    except Exception:
        print(text.encode('ascii', 'replace').decode('ascii'))


async def fetch_and_parse_signals():
    """Fetch messages from the last 24 hours and extract signals"""

    # Load config
    config_path = project_root / 'config' / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Load .env
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv(project_root / 'config' / '.env')

    # Telegram credentials
    api_id = int(os.getenv('TELEGRAM_API_ID', config['telegram']['api_id']))
    api_hash = os.getenv('TELEGRAM_API_HASH', config['telegram']['api_hash'])
    session_path = project_root / 'sessions' / config['telegram']['session_name']

    # Get enabled channels
    enabled_channels = [
        ch['username'] for ch in config['telegram']['channels']
        if ch.get('enabled', True)
    ]

    safe_print(f"Fetching messages from channels: {enabled_channels}")
    safe_print(f"Time range: last 24 hours")
    safe_print("-" * 60)

    # Initialize extractor
    extraction_config = config.get('extraction', {})
    # Add channel confidence mapping
    channel_confidence = {
        ch['username']: ch.get('confidence', 1.0)
        for ch in config['telegram']['channels']
    }
    extraction_config['channel_confidence'] = channel_confidence
    extractor = SignalExtractor(extraction_config)

    # Initialize CSV writer
    csv_path = os.path.expandvars(config['output']['csv']['file_path'])
    csv_writer = CSVWriter(csv_path)

    # Connect to Telegram
    client = TelegramClient(str(session_path), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        safe_print("ERROR: Not authorized. Please run the main app first to authenticate.")
        return

    me = await client.get_me()
    safe_print(f"Logged in as: {me.first_name} ({me.phone})")
    safe_print("-" * 60)

    # Calculate time range (last 24 hours)
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    total_messages = 0
    signals_found = 0
    signals_extracted = []

    for channel_username in enabled_channels:
        safe_print(f"\nFetching from @{channel_username}...")

        try:
            entity = await client.get_entity(channel_username)

            # Fetch messages from last 24 hours
            messages = []
            async for message in client.iter_messages(entity, offset_date=now, reverse=False):
                if message.date < since:
                    break
                if message.text:
                    messages.append(message)

            safe_print(f"  Found {len(messages)} messages in last 24 hours")
            total_messages += len(messages)

            # Process each message
            for message in messages:
                text = message.text
                if not text:
                    continue

                # Quick check if it looks like a signal
                if not extractor.is_signal(text):
                    continue

                safe_print(f"\n  [MSG {message.id}] Potential signal detected:")
                preview = text[:100] + '...' if len(text) > 100 else text
                safe_print(f"  {preview}")

                try:
                    signal = extractor.extract_signal(
                        text=text,
                        message_id=message.id,
                        channel_username=channel_username,
                        timestamp=message.date
                    )

                    entry_display = signal.entry_price or f"{signal.entry_price_min}-{signal.entry_price_max}"
                    safe_print(f"  [OK] SIGNAL: {signal.symbol} {signal.direction} @ {entry_display}")
                    safe_print(f"       SL: {signal.stop_loss}, TPs: {signal.take_profits}")
                    safe_print(f"       Confidence: {signal.confidence_score:.2f}")

                    signals_found += 1
                    signals_extracted.append(signal)

                    # Write to CSV
                    csv_writer.write_signal(signal)

                except ValueError as e:
                    safe_print(f"  [FAIL] Extraction failed: {e}")
                except Exception as e:
                    safe_print(f"  [ERROR] {e}")

        except Exception as e:
            safe_print(f"  ERROR accessing channel: {e}")

    await client.disconnect()

    safe_print("\n" + "=" * 60)
    safe_print("SUMMARY")
    safe_print("=" * 60)
    safe_print(f"Total messages scanned: {total_messages}")
    safe_print(f"Signals extracted: {signals_found}")

    if signals_extracted:
        safe_print(f"\nExtracted signals written to: {csv_path}")
        safe_print("\nSignals found:")
        for s in signals_extracted:
            entry = s.entry_price or f"{s.entry_price_min}-{s.entry_price_max}"
            safe_print(f"  - {s.symbol} {s.direction} @ {entry} (conf: {s.confidence_score:.2f})")


if __name__ == '__main__':
    asyncio.run(fetch_and_parse_signals())
