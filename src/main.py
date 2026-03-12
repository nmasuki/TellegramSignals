"""Main application entry point for Telegram Signal Extractor"""
import asyncio
import logging
import signal as sig
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.config_manager import ConfigManager
from src.utils.logging_setup import setup_logging, get_logger
from src.telegram.client import TelegramListener
from src.extraction.extractor import SignalExtractor
from src.storage.error_logger import ErrorLogger
from src.server.signal_store import SignalStore
from src.server.signal_server import SignalServer
from src.trading.mt5_executor import MT5Executor


# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_flag
    print("\n\nShutdown signal received. Gracefully stopping...")
    shutdown_flag = True


class SignalExtractorApp:
    """Main application class"""

    def __init__(self, config_path: str = None):
        """
        Initialize application

        Args:
            config_path: Path to config.yaml file
        """
        # Load configuration
        self.config = ConfigManager(config_path=config_path)

        # Setup logging
        setup_logging(self.config.get('logging', {}), self.config.project_root)
        self.logger = get_logger(__name__)

        self.logger.info("=" * 60)
        self.logger.info("Telegram Signal Extractor Starting...")
        self.logger.info("=" * 60)

        # Initialize components
        self._init_components()

        # Stats
        self.stats = {
            'messages_processed': 0,
            'signals_extracted': 0,
            'extraction_errors': 0,
        }

        # Track processed messages to avoid duplicates (message_id -> content hash)
        # Load existing message IDs from signal store to prevent duplicates on restart
        existing_ids = self.signal_store.get_all_message_ids()
        self._processed_messages = {msg_id: True for msg_id in existing_ids}
        if existing_ids:
            self.logger.info(f"Loaded {len(existing_ids)} existing message IDs from signal store")

    def _init_components(self):
        """Initialize all application components"""
        self.logger.info("Initializing components...")

        # Get configurations
        telegram_config = self.config.get_telegram_config()
        extraction_config = self.config.get_extraction_config()

        # Initialize Telegram client
        self.telegram_client = TelegramListener(
            api_id=telegram_config['api_id'],
            api_hash=telegram_config['api_hash'],
            session_path=self.config.get_session_path()
        )

        # Initialize signal extractor
        self.signal_extractor = SignalExtractor(extraction_config)

        # Initialize error logger
        self.error_logger = ErrorLogger(
            file_path=self.config.get_error_log_path(),
            encoding=self.config.get('output.error_log.encoding', 'utf-8')
        )

        # Initialize HTTP server for MT5 EA integration
        server_config = self.config.get('server', {})
        persistence_path = str(self.config.project_root / 'data' / 'signal_store.json')

        self.signal_store = SignalStore(
            persistence_path=persistence_path,
            max_age_hours=server_config.get('max_signal_age_hours', 24)
        )

        self.signal_server = SignalServer(
            signal_store=self.signal_store,
            host=server_config.get('host', '0.0.0.0'),
            port=server_config.get('port', 4726)  # GRAM in leetspeak
        )

        # Initialize MT5 trade executor
        trading_config = self.config.get('trading', {})
        self.mt5_executor = MT5Executor(trading_config)

        self.logger.info("Components initialized successfully")

    async def on_new_message(self, message, chat):
        """
        Handle new message from Telegram

        Args:
            message: Telegram message object
            chat: Telegram chat object
        """
        try:
            self.stats['messages_processed'] += 1

            # Get message details
            message_text = message.text or message.message or ""
            channel_username = getattr(chat, 'username', 'unknown')
            message_id = message.id
            timestamp = message.date

            # Quick check if it's a signal
            if not self.signal_extractor.is_signal(message_text):
                self.logger.debug(f"Message {message_id} is not a signal, skipping")
                return

            # Skip if same message with same content was already processed
            content_hash = hash(message_text)
            if self._processed_messages.get(message_id) == content_hash:
                self.logger.debug(f"Skipping duplicate message {message_id}")
                return

            is_edit = message_id in self._processed_messages
            if is_edit:
                self.logger.info(f"Processing edited signal from @{channel_username}")
            else:
                self.logger.info(f"Processing potential signal from @{channel_username}")

            # Extract signal
            try:
                signal = self.signal_extractor.extract_signal(
                    text=message_text,
                    message_id=message_id,
                    channel_username=channel_username,
                    timestamp=timestamp
                )

                # Mark as processed with content hash
                self._processed_messages[message_id] = content_hash

                # Add to signal store for API
                if self.signal_store.add_signal(signal):
                    self.logger.info(f"  Signal added to store (pending)")

                # Execute trades directly via MT5
                if self.mt5_executor.enabled:
                    positions = self.mt5_executor.execute_signal(signal)
                    if positions:
                        self.logger.info(
                            f"  Opened {len(positions)} positions for "
                            f"{signal.direction} {signal.symbol} "
                            f"({', '.join(p.tp_label for p in positions)})"
                        )

                self.stats['signals_extracted'] += 1

                self.logger.info(
                    f"✓ Signal extracted and saved: {signal.symbol} {signal.direction} "
                    f"(confidence: {signal.confidence_score:.2f})"
                )

            except ValueError as e:
                # Extraction failed or low confidence
                self.stats['extraction_errors'] += 1

                error = self.signal_extractor.create_extraction_error(
                    text=message_text,
                    message_id=message_id,
                    channel_username=channel_username,
                    timestamp=timestamp,
                    error_reason=str(e)
                )

                self.error_logger.log_error(error)

                self.logger.warning(f"✗ Extraction failed: {e}")

        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            self.error_logger.log_exception(e, {
                'message_id': message.id,
                'channel': getattr(chat, 'username', 'unknown'),
            })

    async def fetch_historical_signals(self, hours: int = 24):
        """
        Fetch and process historical messages on startup.

        Args:
            hours: Number of hours to look back
        """
        self.logger.info(f"Fetching historical messages from last {hours} hours...")

        historical_count = 0
        signals_found = 0

        async for message, chat in self.telegram_client.fetch_historical_messages(hours=hours):
            try:
                historical_count += 1
                message_text = message.text or ""
                channel_username = getattr(chat, 'username', 'unknown')

                # Quick check if it's a signal
                if not self.signal_extractor.is_signal(message_text):
                    continue

                # Skip if already processed (check by message_id)
                if message.id in self._processed_messages:
                    continue

                # Try to extract signal
                try:
                    signal = self.signal_extractor.extract_signal(
                        text=message_text,
                        message_id=message.id,
                        channel_username=channel_username,
                        timestamp=message.date
                    )

                    # Mark as processed
                    self._processed_messages[message.id] = hash(message_text)

                    # Add to signal store for API
                    self.signal_store.add_signal(signal)

                    signals_found += 1
                    self.stats['signals_extracted'] += 1

                    self.logger.info(
                        f"[Historical] Signal: {signal.symbol} {signal.direction} "
                        f"@ {signal.entry_price or f'{signal.entry_price_min}-{signal.entry_price_max}'} "
                        f"(conf: {signal.confidence_score:.2f})"
                    )

                except ValueError as e:
                    # Low confidence or extraction failed - skip silently for historical
                    self.logger.debug(f"[Historical] Skipped message {message.id}: {e}")

            except Exception as e:
                self.logger.error(f"Error processing historical message: {e}")

        self.logger.info(f"Historical fetch complete: {historical_count} messages scanned, {signals_found} signals found")

    async def run(self):
        """Run the application"""
        try:
            # Connect to Telegram
            telegram_config = self.config.get_telegram_config()
            phone = telegram_config.get('phone')

            await self.telegram_client.connect(phone=phone)

            # Add channels to monitor
            enabled_channels = self.config.get_enabled_channels()

            if not enabled_channels:
                self.logger.error("No enabled channels configured!")
                return

            for channel in enabled_channels:
                channel_username = channel.get('username')
                if channel_username:
                    self.telegram_client.add_channel(channel_username)

                    # Test channel access
                    can_access = await self.telegram_client.test_channel_access(channel_username)
                    if not can_access:
                        self.logger.warning(f"Cannot access channel: @{channel_username}")

            # Fetch historical messages on startup
            startup_fetch_hours = self.config.get('telegram.startup_fetch_hours', 24)
            if startup_fetch_hours > 0:
                await self.fetch_historical_signals(hours=startup_fetch_hours)

            # Register message handlers (new and edited messages)
            self.telegram_client.on_new_message(self.on_new_message)
            self.telegram_client.on_message_edited(self.on_new_message)  # Reuse same handler for edits

            # Start monitoring
            await self.telegram_client.start_monitoring()

            # Connect MT5 executor
            if self.mt5_executor.enabled:
                if self.mt5_executor.connect():
                    self.logger.info("MT5 trade executor connected")
                else:
                    self.logger.warning("MT5 trade executor failed to connect - trades will not be executed")

            # Share executor with signal server for stats
            self.signal_server.set_executor(self.mt5_executor)

            # Start HTTP server for MT5 EA
            self.signal_server.start()

            # Print startup info
            self.print_status()

            # Run until disconnected or shutdown signal
            while not shutdown_flag:
                await asyncio.sleep(1)

            self.logger.info("Shutdown flag set, cleaning up...")

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")

        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)

        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up...")

        # Stop HTTP server
        if hasattr(self, 'signal_server'):
            self.signal_server.stop()

        # Disconnect MT5
        if hasattr(self, 'mt5_executor'):
            self.mt5_executor.disconnect()

        try:
            await self.telegram_client.disconnect()
        except:
            pass

        self.print_stats()
        self.logger.info("Telegram Signal Extractor stopped")

    def print_status(self):
        """Print current status"""
        channels = self.telegram_client.channels
        error_count = self.error_logger.get_error_count()
        store_stats = self.signal_store.get_stats()

        print("\n" + "=" * 60)
        print("TELEGRAM SIGNAL EXTRACTOR - RUNNING")
        print("=" * 60)
        print(f"Monitoring {len(channels)} channel(s):")
        for ch in channels:
            print(f"  - @{ch}")
        print(f"\nExtraction errors logged: {error_count}")
        print(f"Min confidence threshold: {self.config.get_min_confidence()}")
        print(f"\nSignal API Server:")
        print(f"  URL: http://localhost:4726/signals")
        print(f"  Total signals: {store_stats['total']}")
        print(f"  Pending: {store_stats['pending']}")
        print(f"  Acknowledged: {store_stats['acknowledged']}")

        # Trading status
        if self.mt5_executor.enabled:
            trading_stats = self.mt5_executor.get_stats()
            print(f"\nMT5 Trade Executor:")
            print(f"  Connected: {trading_stats['connected']}")
            print(f"  Open positions: {trading_stats['opened_position_count']}")
            print(f"  Lot size: {trading_stats['lot_size']}")
            print(f"  Max positions: {trading_stats['max_positions']}")
        else:
            print(f"\nMT5 Trade Executor: disabled")

        print("\nPress Ctrl+C to stop")
        print("=" * 60 + "\n")

    def print_stats(self):
        """Print statistics"""
        print("\n" + "=" * 60)
        print("SESSION STATISTICS")
        print("=" * 60)
        print(f"Messages processed: {self.stats['messages_processed']}")
        print(f"Signals extracted: {self.stats['signals_extracted']}")
        print(f"Extraction errors: {self.stats['extraction_errors']}")

        if self.stats['messages_processed'] > 0:
            success_rate = (self.stats['signals_extracted'] /
                          max(1, self.stats['signals_extracted'] + self.stats['extraction_errors'])) * 100
            print(f"Success rate: {success_rate:.1f}%")

        print("=" * 60 + "\n")


def main():
    """Main entry point"""
    # Setup signal handlers
    sig.signal(sig.SIGINT, signal_handler)
    sig.signal(sig.SIGTERM, signal_handler)

    # Create and run app
    app = SignalExtractorApp()

    # Run async main loop
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
