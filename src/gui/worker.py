"""Background worker thread for Telegram monitoring"""
import asyncio
import logging
from PySide6.QtCore import QThread, Signal, QEventLoop
from PySide6.QtWidgets import QInputDialog
from datetime import datetime

from src.telegram.client import TelegramListener
from src.extraction.extractor import SignalExtractor
from src.storage.csv_writer import CSVWriter
from src.storage.error_logger import ErrorLogger
from src.server.signal_store import SignalStore
from src.server.signal_server import SignalServer


class BackgroundWorker(QThread):
    """Background worker thread that runs Telegram client"""

    # Signals for thread-safe communication with GUI
    status_changed = Signal(str)  # Status: connected, warning, error, stopped
    signal_extracted = Signal(dict)  # Signal data
    error_occurred = Signal(str, str)  # Error message, level
    message_received = Signal(str, str)  # Channel, message preview
    stats_updated = Signal(dict)  # Statistics dictionary
    log_message = Signal(str, str)  # Message, level (info/success/warning/error)
    request_auth_code = Signal()  # Request auth code from user
    request_2fa_password = Signal()  # Request 2FA password from user

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = False
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.stats = {
            'messages': 0,
            'extracted': 0,
            'errors': 0,
            'start_time': None
        }

        # Authentication responses (set by GUI thread)
        self._auth_code = None
        self._auth_password = None
        self._auth_event = asyncio.Event()

        # Components (initialized in thread)
        self.telegram_client = None
        self.signal_extractor = None
        self.csv_writer = None
        self.error_logger = None
        self.signal_store = None
        self.signal_server = None

    def run(self):
        """Run the worker thread"""
        try:
            self.running = True
            self.log_message.emit("Starting background worker...", "info")

            # Run asyncio event loop
            asyncio.run(self.main_loop())

        except Exception as e:
            self.logger.error(f"Worker thread error: {e}", exc_info=True)
            self.error_occurred.emit(f"Worker error: {str(e)}", "error")
        finally:
            self.status_changed.emit("stopped")
            self.log_message.emit("Background worker stopped", "info")

    async def main_loop(self):
        """Main async loop"""
        try:
            # Initialize components
            await self.initialize_components()

            # Record start time
            self.stats['start_time'] = datetime.now()

            # Connect to Telegram
            self.log_message.emit("Connecting to Telegram...", "info")
            self.status_changed.emit("connecting")

            phone = self.config.get('telegram.phone')
            await self.telegram_client.connect(
                phone=phone,
                code_callback=self._get_auth_code,
                password_callback=self._get_2fa_password
            )

            self.status_changed.emit("connected")
            self.log_message.emit("Successfully connected to Telegram", "success")

            # Add channels
            channels = self.config.get_enabled_channels()
            for channel in channels:
                username = channel.get('username')
                if username:
                    self.telegram_client.add_channel(username)  # Not async, don't await
                    self.log_message.emit(f"Monitoring channel: @{username}", "info")

            # Register message handler
            self.telegram_client.on_new_message(self.on_new_message)

            # Start monitoring
            await self.telegram_client.start_monitoring()

            self.log_message.emit("Message monitoring started", "success")

            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)

                # Emit stats periodically
                self.emit_stats()

        except Exception as e:
            self.logger.error(f"Main loop error: {e}", exc_info=True)
            self.error_occurred.emit(f"Connection error: {str(e)}", "error")
            self.status_changed.emit("error")
        finally:
            # Cleanup
            if self.signal_server:
                self.signal_server.stop()
                self.log_message.emit("Signal server stopped", "info")

            if self.telegram_client:
                await self.telegram_client.disconnect()

    async def initialize_components(self):
        """Initialize backend components"""
        self.log_message.emit("Initializing components...", "info")

        # Signal extractor
        extraction_config = self.config.get_extraction_config()
        self.signal_extractor = SignalExtractor(extraction_config)
        self.logger.info("Signal extractor initialized")

        # CSV writer
        csv_path = self.config.get_csv_path()
        self.csv_writer = CSVWriter(csv_path)
        self.logger.info(f"CSV writer initialized: {csv_path}")

        # Error logger
        error_log_path = self.config.get_error_log_path()
        self.error_logger = ErrorLogger(error_log_path)
        self.logger.info(f"Error logger initialized: {error_log_path}")

        # Telegram client
        telegram_config = self.config.get_telegram_config()
        session_path = self.config.get_session_path()

        self.telegram_client = TelegramListener(
            api_id=telegram_config['api_id'],
            api_hash=telegram_config['api_hash'],
            session_path=session_path
        )
        self.logger.info("Telegram client initialized")

        # Signal store and HTTP server for MT5 EA integration
        persistence_path = str(self.config.project_root / 'data' / 'signal_store.json')
        server_port = self.config.get('server.port', 4726)

        self.signal_store = SignalStore(
            persistence_path=persistence_path,
            max_age_hours=24
        )
        self.logger.info("Signal store initialized")

        self.signal_server = SignalServer(
            signal_store=self.signal_store,
            host="0.0.0.0",
            port=server_port
        )
        # Start server
        self.signal_server.start()
        self.log_message.emit(f"Signal server started on port {server_port}", "success")
        self.logger.info(f"Signal server started on http://0.0.0.0:{server_port}")

    async def on_new_message(self, message, chat):
        """Handle new message from Telegram"""
        try:
            # Get message info
            message_text = message.text or ""
            channel_username = getattr(chat, 'username', 'Unknown')
            message_id = message.id
            timestamp = message.date

            self.stats['messages'] += 1

            # Emit message received
            preview = message_text[:50] + "..." if len(message_text) > 50 else message_text
            self.message_received.emit(channel_username, preview)

            # Check if this is a signal
            if self.signal_extractor.is_signal(message_text):
                self.log_message.emit(f"Processing potential signal from @{channel_username}", "info")

                try:
                    # Extract signal (may raise ValueError for low confidence)
                    signal = self.signal_extractor.extract_signal(
                        message_text,
                        message_id,
                        channel_username,
                        timestamp
                    )

                    # Valid signal - save it
                    self.csv_writer.write_signal(signal)

                    # Add to signal store for MT5 EA
                    if self.signal_store.add_signal(signal):
                        self.logger.info(f"  Signal added to MT5 store (pending)")

                    self.stats['extracted'] += 1

                    # Emit signal extracted
                    signal_data = {
                        'timestamp': signal.timestamp,
                        'channel_username': signal.channel_username,
                        'symbol': signal.symbol,
                        'direction': signal.direction,
                        'entry_price': signal.entry_price,
                        'entry_price_min': signal.entry_price_min,
                        'entry_price_max': signal.entry_price_max,
                        'stop_loss': signal.stop_loss,
                        'take_profit_1': signal.take_profits[0] if len(signal.take_profits) > 0 else None,
                        'take_profit_2': signal.take_profits[1] if len(signal.take_profits) > 1 else None,
                        'take_profit_3': signal.take_profits[2] if len(signal.take_profits) > 2 else None,
                        'take_profit_4': signal.take_profits[3] if len(signal.take_profits) > 3 else None,
                        'confidence_score': signal.confidence_score
                    }

                    self.signal_extracted.emit(signal_data)

                    self.log_message.emit(
                        f"Signal extracted: {signal.symbol} {signal.direction} (confidence: {signal.confidence_score:.2f})",
                        "success"
                    )

                except ValueError as e:
                    # Low confidence or extraction failed - this is expected, not an error
                    self.logger.debug(f"Message skipped: {e}")
                    self.log_message.emit(
                        f"Skipped message from @{channel_username}: {e}",
                        "info"
                    )

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            self.error_occurred.emit(f"Error processing message: {str(e)}", "error")

    def emit_stats(self):
        """Emit current statistics"""
        # Calculate success rate
        total_signals = self.stats['extracted'] + self.stats['errors']
        if total_signals > 0:
            success_rate = (self.stats['extracted'] / total_signals) * 100
        else:
            success_rate = -1  # No data yet

        # Calculate uptime
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            uptime_str = "00:00:00"

        stats_dict = {
            'messages': self.stats['messages'],
            'extracted': self.stats['extracted'],
            'errors': self.stats['errors'],
            'success_rate': success_rate,
            'uptime': uptime_str
        }

        self.stats_updated.emit(stats_dict)

    def stop(self):
        """Stop the worker"""
        self.log_message.emit("Stopping background worker...", "info")
        self.running = False

    def provide_auth_code(self, code: str):
        """Provide auth code from GUI (called by main thread)"""
        self._auth_code = code
        self._auth_event.set()

    def provide_2fa_password(self, password: str):
        """Provide 2FA password from GUI (called by main thread)"""
        self._auth_password = password
        self._auth_event.set()

    async def _get_auth_code(self):
        """Request auth code from GUI and wait for response"""
        self._auth_code = None
        self._auth_event.clear()
        self.request_auth_code.emit()

        # Wait for GUI to provide the code
        await self._auth_event.wait()
        return self._auth_code

    async def _get_2fa_password(self):
        """Request 2FA password from GUI and wait for response"""
        self._auth_password = None
        self._auth_event.clear()
        self.request_2fa_password.emit()

        # Wait for GUI to provide the password
        await self._auth_event.wait()
        return self._auth_password
