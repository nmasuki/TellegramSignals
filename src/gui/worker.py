"""Background worker thread for Telegram monitoring"""
import asyncio
import logging
from PySide6.QtCore import QThread, Signal, QEventLoop
from PySide6.QtWidgets import QInputDialog
from datetime import datetime, timezone, timedelta

from src.telegram.client import TelegramListener
from src.extraction.extractor import SignalExtractor
from src.storage.csv_writer import CSVWriter
from src.storage.error_logger import ErrorLogger
from src.server.signal_store import SignalStore
from src.server.signal_server import SignalServer
from src.trading.mt5_executor import MT5Executor


class BackgroundWorker(QThread):
    """Background worker thread that runs Telegram client"""

    # Signals for thread-safe communication with GUI
    status_changed = Signal(str)  # Status: connected, warning, error, stopped
    signal_extracted = Signal(dict)  # Signal data
    signal_status_updated = Signal(int, str)  # message_id, execution_status
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

        # Cleanup tracking
        self._last_cleanup_time = None
        self._cleanup_interval_hours = 1  # Run cleanup every hour

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
        self.mt5_executor = None

        # Track processed messages to avoid duplicates (message_id -> content hash)
        self._processed_messages = {}

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

            # Register message handlers (new and edited messages)
            self.telegram_client.on_new_message(self.on_new_message)
            self.telegram_client.on_message_edited(self.on_new_message)  # Reuse same handler for edits

            # Start monitoring
            await self.telegram_client.start_monitoring()

            self.log_message.emit("Message monitoring started", "success")

            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)

                # Emit stats periodically
                self.emit_stats()

                # Periodic cleanup of old CSV records
                self._run_periodic_cleanup()

        except Exception as e:
            self.logger.error(f"Main loop error: {e}", exc_info=True)
            self.error_occurred.emit(f"Connection error: {str(e)}", "error")
            self.status_changed.emit("error")
        finally:
            # Cleanup
            if self.signal_server:
                self.signal_server.stop()
                self.log_message.emit("Signal server stopped", "info")

            if self.mt5_executor:
                self.mt5_executor.disconnect()

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

        # Initialize MT5 trade executor
        trading_config = self.config.get('trading', {})
        self.mt5_executor = MT5Executor(trading_config)
        if self.mt5_executor.enabled:
            if self.mt5_executor.connect():
                self.logger.info("MT5 trade executor connected")
                self.log_message.emit("MT5 trade executor connected", "success")
            else:
                self.logger.warning("MT5 trade executor failed to connect - trades will not be executed")
                self.log_message.emit("MT5 executor failed to connect", "warning")
            # Share executor with signal server for stats/positions
            self.signal_server.set_executor(self.mt5_executor)
        else:
            self.logger.info("MT5 trade executor disabled")

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

            # Check for close/break-even/partial-close signals first
            is_close = self.signal_extractor.pattern_matcher.is_close_signal(message_text)
            is_be = self.signal_extractor.pattern_matcher.is_break_even_signal(message_text)
            is_tp_hit = self.signal_extractor.pattern_matcher.is_tp_hit_signal(message_text)
            is_partial = self.signal_extractor.pattern_matcher.is_partial_close_signal(message_text)

            if is_close or is_be or is_tp_hit or is_partial:
                close_dir = self.signal_extractor.pattern_matcher.extract_close_direction(message_text)
                close_sym = self.signal_extractor.pattern_matcher.extract_close_symbol(message_text)

                if self.mt5_executor and self.mt5_executor.enabled:
                    if is_partial and is_be:
                        # Partial close + BE: close higher entries, BE on lowest
                        closed, be_count = self.mt5_executor.partial_close_positions(
                            channel_username=channel_username, symbol=close_sym
                        )
                        action = f"Partial close: {closed} closed, {be_count} moved to BE"
                        self.log_message.emit(action, "success" if closed + be_count > 0 else "warning")
                    elif is_partial:
                        # Partial close without explicit BE
                        closed, be_count = self.mt5_executor.partial_close_positions(
                            channel_username=channel_username, symbol=close_sym
                        )
                        action = f"Partial close: {closed} closed, kept lowest entry"
                        self.log_message.emit(action, "success" if closed > 0 else "warning")
                    elif is_be and not is_close:
                        count = self.mt5_executor.move_sl_to_break_even(
                            channel_username=channel_username, symbol=close_sym
                        )
                        action = f"Break-even applied to {count} positions"
                        self.log_message.emit(action, "success" if count > 0 else "warning")
                    elif is_close or is_tp_hit:
                        closed = self.mt5_executor.close_positions(
                            channel_username=channel_username,
                            direction=close_dir,
                            symbol=close_sym,
                        )
                        cancelled = self.mt5_executor.cancel_pending_orders(
                            channel_username=channel_username,
                            symbol=close_sym,
                        )
                        action = f"Closed {closed} positions, cancelled {cancelled} pending orders"
                        self.log_message.emit(action, "success" if closed + cancelled > 0 else "warning")
                else:
                    action_type = "Partial close" if is_partial else ("Break-even" if is_be else "Close")
                    self.log_message.emit(
                        f"{action_type} signal from @{channel_username} (MT5 not enabled)",
                        "warning"
                    )

                self.logger.info(
                    f"  Management signal from @{channel_username}: "
                    f"close={is_close}, BE={is_be}, TP_hit={is_tp_hit}, partial={is_partial}"
                )
                return  # Don't process as a trade signal

            # Check if this is a signal
            if self.signal_extractor.is_signal(message_text):
                # Skip if same message with same content was already processed
                content_hash = hash(message_text)
                if self._processed_messages.get(message_id) == content_hash:
                    self.logger.debug(f"Skipping duplicate message {message_id}")
                    return

                is_edit = message_id in self._processed_messages
                if is_edit:
                    self.log_message.emit(f"Processing edited signal from @{channel_username}", "info")
                else:
                    self.log_message.emit(f"Processing potential signal from @{channel_username}", "info")

                try:
                    # Extract signal
                    signal = self.signal_extractor.extract_signal(
                        message_text,
                        message_id,
                        channel_username,
                        timestamp
                    )

                    # Mark as processed with content hash
                    self._processed_messages[message_id] = content_hash

                    # Always save to CSV for record-keeping
                    self.csv_writer.write_signal(signal)

                    # Low-confidence signals: show in table but skip execution and HTTP serving
                    is_low_conf = signal.execution_status == "LOW_CONF"

                    # Only add to signal store (HTTP server) if confidence is sufficient
                    if not is_low_conf:
                        if self.signal_store.add_signal(signal):
                            self.logger.info(f"  Signal added to MT5 store (pending)")

                    # Skip execution for low-confidence signals
                    if is_low_conf:
                        self.logger.info(
                            f"  Low confidence ({signal.confidence_score:.2f}), showing but not executing"
                        )
                        self.log_message.emit(
                            f"Low confidence signal: {signal.symbol} {signal.direction} "
                            f"({signal.confidence_score:.2f})",
                            "warning"
                        )

                    else:
                        # Check signal staleness - skip if too old (network delay, sleep, etc.)
                        max_age_minutes = self.config.get('trading.max_signal_age_minutes', 10)
                        sig_ts = signal.timestamp if signal.timestamp.tzinfo else signal.timestamp.replace(tzinfo=timezone.utc)
                        signal_age = datetime.now(timezone.utc) - sig_ts
                        is_stale = signal_age > timedelta(minutes=max_age_minutes)

                        if is_stale:
                            signal.execution_status = "SKIPPED"
                            age_str = f"{signal_age.total_seconds() / 60:.1f}min"
                            self.logger.info(
                                f"  Signal too old ({age_str} > {max_age_minutes}min), skipping execution"
                            )
                            self.log_message.emit(
                                f"Stale signal skipped ({age_str} old): {signal.symbol} {signal.direction}",
                                "warning"
                            )

                        # Determine execution status
                        elif self.mt5_executor and self.mt5_executor.enabled:
                            # Fill missing SL/TP using R:R before validation
                            self.mt5_executor._fill_missing_sl_tp(signal)
                            # Pre-check if signal is tradeable before attempting execution
                            reject_reason = self.mt5_executor._validate_for_trading(signal)
                            if reject_reason:
                                signal.execution_status = "SKIPPED"
                                self.logger.info(f"  Signal not tradeable: {reject_reason}")
                                self.log_message.emit(
                                    f"Signal skipped: {signal.symbol} {signal.direction} ({reject_reason})",
                                    "warning"
                                )
                            else:
                                # Signal is valid for trading - attempt execution
                                positions = self.mt5_executor.execute_signal(signal)
                                if positions:
                                    signal.execution_status = "EXECUTED"
                                    self.logger.info(
                                        f"  Opened {len(positions)} MT5 positions for "
                                        f"{signal.symbol} {signal.direction}"
                                    )
                                    self.log_message.emit(
                                        f"Opened {len(positions)} positions: {signal.symbol} {signal.direction}",
                                        "success"
                                    )
                                else:
                                    signal.execution_status = "FAILED"
                                    self.logger.warning(
                                        f"  MT5 execution failed for {signal.symbol} {signal.direction}"
                                    )
                                    self.log_message.emit(
                                        f"Trade failed: {signal.symbol} {signal.direction}",
                                        "error"
                                    )
                        else:
                            # MT5 executor not enabled — still check if signal would be tradeable
                            if self.mt5_executor:
                                self.mt5_executor._fill_missing_sl_tp(signal)
                                reject_reason = self.mt5_executor._validate_for_trading(signal)
                                if reject_reason:
                                    signal.execution_status = "SKIPPED"
                                    self.logger.info(f"  Signal not tradeable: {reject_reason}")
                                else:
                                    signal.execution_status = "PENDING"
                            else:
                                signal.execution_status = "PENDING"

                    # Update CSV and store with execution status
                    self.csv_writer.write_signal(signal)
                    if not is_low_conf:
                        self.signal_store.add_signal(signal)

                    # Notify GUI of status change
                    self.signal_status_updated.emit(signal.message_id, signal.execution_status)

                    self.stats['extracted'] += 1

                    # Emit signal extracted
                    signal_data = {
                        'message_id': signal.message_id,
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
                        'confidence_score': signal.confidence_score,
                        'execution_status': signal.execution_status
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
                    # Log to error file for review
                    if self.error_logger:
                        from src.extraction.models import ExtractionError
                        self.error_logger.log_error(ExtractionError(
                            message_id=message_id,
                            channel_username=channel_username,
                            timestamp=timestamp,
                            raw_message=message_text,
                            error_reason=str(e),
                        ))

        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            self.error_occurred.emit(f"Error processing message: {str(e)}", "error")
            if self.error_logger:
                self.error_logger.log_exception(e, {
                    'channel_username': channel_username,
                })

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

    def _run_periodic_cleanup(self):
        """Run periodic cleanup of old CSV records"""
        now = datetime.now()

        # Run cleanup on first call or after interval has passed
        if self._last_cleanup_time is None:
            # Run initial cleanup on startup
            self._perform_cleanup()
            self._last_cleanup_time = now
        else:
            # Check if interval has passed
            hours_since_cleanup = (now - self._last_cleanup_time).total_seconds() / 3600
            if hours_since_cleanup >= self._cleanup_interval_hours:
                self._perform_cleanup()
                self._last_cleanup_time = now

    def _perform_cleanup(self):
        """Perform the actual cleanup"""
        try:
            if self.csv_writer:
                removed = self.csv_writer.cleanup_old_records(max_age_hours=12)
                if removed > 0:
                    self.log_message.emit(f"Cleaned up {removed} old signal records (>12h)", "info")
        except Exception as e:
            self.logger.error(f"CSV cleanup error: {e}")

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
