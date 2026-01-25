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
from src.storage.csv_writer import CSVWriter
from src.storage.error_logger import ErrorLogger
from src.server.signal_store import SignalStore
from src.server.signal_server import SignalServer


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

        # Initialize CSV writer
        self.csv_writer = CSVWriter(
            file_path=self.config.get_csv_path(),
            encoding=self.config.get('output.csv.encoding', 'utf-8')
        )

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

            self.logger.info(f"Processing potential signal from @{channel_username}")

            # Extract signal
            try:
                signal = self.signal_extractor.extract_signal(
                    text=message_text,
                    message_id=message_id,
                    channel_username=channel_username,
                    timestamp=timestamp
                )

                # Write to CSV
                self.csv_writer.write_signal(signal)

                # Add to signal store for MT5 EA
                if self.signal_store.add_signal(signal):
                    self.logger.info(f"  Signal added to MT5 store (pending)")

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

            # Register message handler
            self.telegram_client.on_new_message(self.on_new_message)

            # Start monitoring
            await self.telegram_client.start_monitoring()

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

        try:
            await self.telegram_client.disconnect()
        except:
            pass

        self.print_stats()
        self.logger.info("Telegram Signal Extractor stopped")

    def print_status(self):
        """Print current status"""
        channels = self.telegram_client.channels
        csv_count = self.csv_writer.get_signal_count()
        error_count = self.error_logger.get_error_count()
        store_stats = self.signal_store.get_stats()

        print("\n" + "=" * 60)
        print("TELEGRAM SIGNAL EXTRACTOR - RUNNING")
        print("=" * 60)
        print(f"Monitoring {len(channels)} channel(s):")
        for ch in channels:
            print(f"  - @{ch}")
        print(f"\nSignals in CSV: {csv_count}")
        print(f"Extraction errors logged: {error_count}")
        print(f"Min confidence threshold: {self.config.get_min_confidence()}")
        print(f"\nMT5 Signal Server:")
        print(f"  URL: http://localhost:4726/signals")
        print(f"  Pending signals: {store_stats['pending']}")
        print(f"  Acknowledged: {store_stats['acknowledged']}")
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
