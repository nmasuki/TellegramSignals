"""MT5 Trade Executor - opens trades directly from extracted signals"""
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

from ..extraction.models import Signal


logger = logging.getLogger(__name__)


@dataclass
class OpenedPosition:
    """Tracks a position opened from a signal"""
    ticket: int
    signal_message_id: int
    channel_username: str
    symbol: str
    direction: str
    volume: float
    open_price: float
    stop_loss: Optional[float]
    take_profit: float  # The specific TP this position targets
    tp_label: str = ""  # e.g. "TP1", "TP2"
    opened_at: datetime = field(default_factory=datetime.now)
    status: str = "open"  # open, closed, error


class MT5Executor:
    """
    Executes trades on MetaTrader 5 based on extracted signals.

    Connects to a running MT5 terminal and opens positions directly.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MT5 executor.

        Args:
            config: Trading configuration dict with keys:
                - enabled: bool
                - lot_size: float (default 0.01)
                - max_positions: int (max simultaneous positions)
                - allowed_symbols: list of symbols to trade
                - slippage: int (max slippage in points)
                - magic_number: int (EA magic number for identification)
                - mt5_path: str (optional path to MT5 terminal)
        """
        self.enabled = config.get('enabled', False)
        self.lot_size = config.get('lot_size', 0.01)
        self.positions_per_signal = config.get('positions_per_signal', 6)
        self.max_positions = config.get('max_positions', 30)
        self.allowed_symbols = config.get('allowed_symbols', ['XAUUSD'])
        self.slippage = config.get('slippage', 20)
        self.magic_number = config.get('magic_number', 472600)
        self.mt5_path = config.get('mt5_path', None)
        self.min_confidence = config.get('min_confidence', 0.80)

        self._lock = threading.Lock()
        self._positions: List[OpenedPosition] = []
        self._connected = False

        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 package not installed. Run: pip install MetaTrader5")
            self.enabled = False

    def connect(self) -> bool:
        """Connect to MT5 terminal. Returns True if successful."""
        if not self.enabled or not MT5_AVAILABLE:
            return False

        try:
            kwargs = {}
            if self.mt5_path:
                kwargs['path'] = self.mt5_path

            if not mt5.initialize(**kwargs):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False

            terminal_info = mt5.terminal_info()
            account_info = mt5.account_info()

            if terminal_info and account_info:
                logger.info(
                    f"MT5 connected: {account_info.server}, "
                    f"Account #{account_info.login}, "
                    f"Balance: {account_info.balance} {account_info.currency}"
                )
                self._connected = True
                return True
            else:
                logger.error("MT5 connected but could not get account info")
                return False

        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from MT5."""
        if MT5_AVAILABLE and self._connected:
            mt5.shutdown()
            self._connected = False
            logger.info("MT5 disconnected")

    def execute_signal(self, signal: Signal) -> Optional[List[OpenedPosition]]:
        """
        Execute trades based on an extracted signal.

        Opens multiple positions (positions_per_signal) distributed evenly
        across all take profit levels. Each position uses lot_size as volume.

        E.g., 6 positions with 3 TPs -> 2 positions per TP:
          - 2x with TP1, 2x with TP2, 2x with TP3

        Args:
            signal: Extracted signal from Telegram

        Returns:
            List of OpenedPositions if any trades opened, None otherwise
        """
        if not self.enabled:
            logger.debug("MT5 executor disabled, skipping trade")
            return None

        if not self._connected:
            logger.warning("MT5 not connected, attempting reconnect...")
            if not self.connect():
                return None

        # Validate signal is tradeable
        reason = self._validate_for_trading(signal)
        if reason:
            logger.info(f"Signal not tradeable: {reason}")
            return None

        with self._lock:
            # Check max positions (need room for all positions_per_signal)
            open_count = self.get_open_position_count()
            slots_available = self.max_positions - open_count
            if slots_available <= 0:
                logger.warning(
                    f"Max positions reached ({open_count}/{self.max_positions}), skipping"
                )
                return None

            # Cap to available slots
            num_positions = min(self.positions_per_signal, slots_available)

            return self._open_positions(signal, num_positions)

    def _validate_for_trading(self, signal: Signal) -> Optional[str]:
        """
        Check if a signal is suitable for trading. Returns reason string if not, None if OK.
        """
        if signal.symbol not in self.allowed_symbols:
            return f"Symbol {signal.symbol} not in allowed list"

        if signal.confidence_score < self.min_confidence:
            return f"Confidence {signal.confidence_score:.2f} below threshold {self.min_confidence}"

        if not signal.direction or signal.direction not in ('BUY', 'SELL'):
            return f"Invalid direction: {signal.direction}"

        if not signal.stop_loss:
            return "No stop loss defined"

        if not signal.take_profits:
            return "No take profits defined"

        return None

    @staticmethod
    def _distribute_positions(num_positions: int, take_profits: List[float]) -> List[tuple]:
        """
        Distribute N positions evenly across take profit levels.

        E.g., 6 positions, 3 TPs -> [(TP1,2), (TP2,2), (TP3,2)]
              6 positions, 4 TPs -> [(TP1,2), (TP2,2), (TP3,1), (TP4,1)]

        Returns list of (tp_price, count, tp_label) tuples.
        """
        num_tps = len(take_profits)
        base_count = num_positions // num_tps
        remainder = num_positions % num_tps

        distribution = []
        for i, tp in enumerate(take_profits):
            # Give extra positions to the earlier TPs (more likely to hit)
            count = base_count + (1 if i < remainder else 0)
            if count > 0:
                distribution.append((tp, count, f"TP{i+1}"))

        return distribution

    def _open_positions(self, signal: Signal, num_positions: int) -> Optional[List[OpenedPosition]]:
        """Open multiple positions distributed across TPs."""
        try:
            symbol = signal.symbol
            direction = signal.direction

            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get tick for {symbol}")
                return None

            # Ensure symbol is visible
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol {symbol}")
                return None

            # Determine order type and price
            if direction == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid

            # Distribute positions across TPs
            distribution = self._distribute_positions(num_positions, signal.take_profits)

            opened = []
            errors = 0

            for tp_price, count, tp_label in distribution:
                for i in range(count):
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": self.lot_size,
                        "type": order_type,
                        "price": price,
                        "sl": signal.stop_loss,
                        "tp": tp_price,
                        "deviation": self.slippage,
                        "magic": self.magic_number,
                        "comment": f"TGS|{signal.channel_username}|{signal.message_id}|{tp_label}",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }

                    result = mt5.order_send(request)

                    if result is None:
                        error = mt5.last_error()
                        logger.error(f"Order send returned None ({tp_label}): {error}")
                        errors += 1
                        continue

                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        logger.error(
                            f"Order failed ({tp_label}): retcode={result.retcode}, "
                            f"comment={result.comment}"
                        )
                        self._positions.append(OpenedPosition(
                            ticket=0,
                            signal_message_id=signal.message_id,
                            channel_username=signal.channel_username,
                            symbol=symbol,
                            direction=direction,
                            volume=self.lot_size,
                            open_price=price,
                            stop_loss=signal.stop_loss,
                            take_profit=tp_price,
                            tp_label=tp_label,
                            status="error",
                        ))
                        errors += 1
                        continue

                    position = OpenedPosition(
                        ticket=result.order,
                        signal_message_id=signal.message_id,
                        channel_username=signal.channel_username,
                        symbol=symbol,
                        direction=direction,
                        volume=result.volume,
                        open_price=result.price,
                        stop_loss=signal.stop_loss,
                        take_profit=tp_price,
                        tp_label=tp_label,
                    )
                    self._positions.append(position)
                    opened.append(position)

                    # Refresh price for next order
                    tick = mt5.symbol_info_tick(symbol)
                    if tick:
                        price = tick.ask if direction == 'BUY' else tick.bid

            # Log summary
            tp_summary = ", ".join(
                f"{count}x {label}@{tp}" for tp, count, label in distribution
            )
            logger.info(
                f"Opened {len(opened)}/{num_positions} positions for "
                f"{direction} {symbol} (errors: {errors}): {tp_summary}"
            )

            return opened if opened else None

        except Exception as e:
            logger.error(f"Error opening positions: {e}", exc_info=True)
            return None

    def get_open_position_count(self) -> int:
        """Get count of currently open positions opened by this executor."""
        if not self._connected or not MT5_AVAILABLE:
            return sum(1 for p in self._positions if p.status == "open")

        try:
            positions = mt5.positions_get()
            if positions is None:
                return 0
            # Count only positions with our magic number
            return sum(1 for p in positions if p.magic == self.magic_number)
        except Exception:
            return sum(1 for p in self._positions if p.status == "open")

    def get_all_positions(self) -> List[dict]:
        """Get all tracked positions as dicts."""
        with self._lock:
            return [
                {
                    "ticket": p.ticket,
                    "signal_message_id": p.signal_message_id,
                    "channel": p.channel_username,
                    "symbol": p.symbol,
                    "direction": p.direction,
                    "volume": p.volume,
                    "open_price": p.open_price,
                    "stop_loss": p.stop_loss,
                    "take_profit": p.take_profit,
                    "tp_label": p.tp_label,
                    "opened_at": p.opened_at.isoformat(),
                    "status": p.status,
                }
                for p in self._positions
            ]

    def get_stats(self) -> dict:
        """Get executor statistics."""
        with self._lock:
            total = len(self._positions)
            opened = sum(1 for p in self._positions if p.status == "open")
            errors = sum(1 for p in self._positions if p.status == "error")

            return {
                "enabled": self.enabled,
                "connected": self._connected,
                "opened_position_count": self.get_open_position_count(),
                "total_trades": total,
                "errors": errors,
                "lot_size": self.lot_size,
                "max_positions": self.max_positions,
            }

    @property
    def is_connected(self) -> bool:
        return self._connected
