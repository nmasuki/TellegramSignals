"""MT5 Trade Executor - opens trades directly from extracted signals"""
import logging
import threading
from datetime import datetime, timedelta
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
    order_type: str = "market"  # "market" or "pending"
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
                - risk_reward_ratio: float (default 2.0)
                - default_tp_pips: float (default 30)
        """
        self.enabled = config.get('enabled', False)
        self.lot_size = config.get('lot_size', 0.01)
        self.min_lot_size = config.get('min_lot_size', 0.01)
        self.max_lot_size = config.get('max_lot_size', 0.05)
        self.positions_per_signal = config.get('positions_per_signal', 6)
        self.max_positions = config.get('max_positions', 30)
        self.allowed_symbols = config.get('allowed_symbols', ['XAUUSD'])
        self.slippage = config.get('slippage', 20)
        self.magic_number = config.get('magic_number', 472600)
        self.mt5_path = config.get('mt5_path', None)
        self.min_confidence = config.get('min_confidence', 0.80)
        self.risk_reward_ratio = config.get('risk_reward_ratio', 2.0)
        self.default_tp_pips = config.get('default_tp_pips', 30)
        self.entry_range_pips = config.get('entry_range_pips', 30)
        self.pending_expiry_minutes = config.get('pending_expiry_minutes', 30)

        self._lock = threading.Lock()
        self._positions: List[OpenedPosition] = []
        self._connected = False
        self._symbol_map: Dict[str, str] = {}  # e.g. {"XAUUSD": "XAUUSD.a", "EURUSD": "EURUSDm"}

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
                self._build_symbol_map()
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

    def _build_symbol_map(self):
        """
        Build mapping from standard symbol names to broker-specific names.

        Brokers often add suffixes like .a, .b, m, .raw, .pro, etc.
        E.g., XAUUSD -> XAUUSDm, EURUSD -> EURUSD.a
        """
        self._symbol_map.clear()
        try:
            all_symbols = mt5.symbols_get()
            if not all_symbols:
                return

            # Build a lookup: lowercase broker symbol -> original broker symbol
            broker_symbols = {s.name.lower(): s.name for s in all_symbols}

            for standard in self.allowed_symbols:
                std_lower = standard.lower()

                # 1. Exact match
                if std_lower in broker_symbols:
                    self._symbol_map[standard] = broker_symbols[std_lower]
                    continue

                # 2. Find broker symbols that start with the standard name (suffix match)
                candidates = [
                    name for lower, name in broker_symbols.items()
                    if lower.startswith(std_lower) and len(lower) - len(std_lower) <= 4
                ]

                if len(candidates) == 1:
                    self._symbol_map[standard] = candidates[0]
                elif len(candidates) > 1:
                    # Prefer shortest (closest to standard name)
                    candidates.sort(key=len)
                    self._symbol_map[standard] = candidates[0]

            # Log mappings
            for std, broker in self._symbol_map.items():
                if std != broker:
                    logger.info(f"Symbol mapped: {std} -> {broker}")

            unmapped = [s for s in self.allowed_symbols if s not in self._symbol_map]
            if unmapped:
                logger.warning(f"No broker symbols found for: {unmapped}")

        except Exception as e:
            logger.error(f"Failed to build symbol map: {e}")

    def resolve_symbol(self, symbol: str) -> Optional[str]:
        """
        Resolve a standard symbol name to the broker's actual symbol.

        Returns the broker symbol, or None if not found.
        """
        # Check cached map first
        if symbol in self._symbol_map:
            return self._symbol_map[symbol]

        # Try live lookup if not in cache (symbol might have been added)
        if self._connected and MT5_AVAILABLE:
            info = mt5.symbol_info(symbol)
            if info is not None:
                self._symbol_map[symbol] = info.name
                return info.name

            # Try prefix search
            all_symbols = mt5.symbols_get(group=f"*{symbol}*")
            if all_symbols:
                candidates = [
                    s.name for s in all_symbols
                    if s.name.upper().startswith(symbol.upper())
                ]
                if candidates:
                    candidates.sort(key=len)
                    self._symbol_map[symbol] = candidates[0]
                    logger.info(f"Symbol resolved: {symbol} -> {candidates[0]}")
                    return candidates[0]

        return None

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

        # Resolve broker symbol (e.g. XAUUSD -> XAUUSDm)
        broker_symbol = self.resolve_symbol(signal.symbol)
        if broker_symbol is None:
            logger.info(f"Signal not tradeable: Symbol {signal.symbol} not found on broker")
            return None

        # Fill missing entry from SL + TP using R:R ratio
        self._fill_missing_entry(signal)

        # Fill missing SL/TP using R:R ratio before validation
        self._fill_missing_sl_tp(signal)

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

            return self._open_positions(signal, num_positions, broker_symbol)

    def _get_pip_size(self, symbol: str) -> Optional[float]:
        """Get pip size for a symbol from MT5. Returns None if unavailable."""
        if not self._connected or not MT5_AVAILABLE:
            return None
        try:
            broker_sym = self.resolve_symbol(symbol) or symbol
            info = mt5.symbol_info(broker_sym)
            if info is None:
                return None
            # pip = 10 * point for most brokers (5-digit forex, 3-digit JPY, 2-digit gold)
            return info.point * 10
        except Exception:
            return None

    @staticmethod
    def _fallback_pip_size(symbol: str) -> float:
        """Estimate pip size from symbol name when MT5 is unavailable."""
        sym = symbol.upper()
        if 'XAU' in sym or 'GOLD' in sym:
            return 0.1  # Gold: point=0.01, pip=0.1
        if 'XAG' in sym or 'SILVER' in sym:
            return 0.01  # Silver
        if 'JPY' in sym:
            return 0.01  # JPY pairs: 3-digit pricing
        if 'BTC' in sym:
            return 1.0  # Bitcoin
        if sym in ('US30', 'DJ30'):
            return 1.0  # US30 index: point=0.1, pip=1.0
        return 0.0001  # Standard forex (5-digit pricing)

    def _compute_lot_size(self, signal: Signal) -> float:
        """
        Scale lot size based on signal confidence score.

        Linearly interpolates between min_lot_size (at min_confidence threshold)
        and max_lot_size (at 1.0 confidence).
        """
        confidence = signal.confidence_score
        conf_floor = self.min_confidence  # e.g. 0.80
        conf_range = 1.0 - conf_floor

        if conf_range <= 0:
            return self.lot_size

        # Scale: 0.0 at min_confidence, 1.0 at confidence=1.0
        scale = max(0.0, min(1.0, (confidence - conf_floor) / conf_range))
        lot = self.min_lot_size + scale * (self.max_lot_size - self.min_lot_size)

        # Round to 2 decimal places (standard MT5 lot precision)
        lot = round(lot, 2)
        lot = max(self.min_lot_size, min(self.max_lot_size, lot))

        logger.info(
            f"Lot size for confidence {confidence:.2f}: {lot} "
            f"(range {self.min_lot_size}-{self.max_lot_size})"
        )
        return lot

    def _fill_missing_entry(self, signal: Signal) -> None:
        """
        Compute entry price from SL and TP1 using R:R ratio when entry is missing.

        Formula: entry = SL + (TP1 - SL) / (1 + R:R)
        Works for both BUY and SELL directions.
        """
        if signal.is_market_order:
            return
        if signal.get_entry_average() is not None:
            return  # Entry already exists
        if signal.stop_loss is None or not signal.take_profits:
            return  # Can't compute without both SL and TP

        sl = signal.stop_loss
        tp1 = signal.take_profits[0]
        rr = self.risk_reward_ratio

        entry = sl + (tp1 - sl) / (1 + rr)
        signal.entry_price = round(entry, 5)

        logger.info(
            f"Computed entry={signal.entry_price:.5f} from SL={sl} and TP1={tp1} "
            f"using R:R={rr} for {signal.symbol} {signal.direction}"
        )

    def _fill_missing_sl_tp(self, signal: Signal) -> None:
        """
        Fill in missing SL/TP using risk:reward ratio and market price.

        Rules (R:R = self.risk_reward_ratio, default 2.0):
          - TP missing, SL present:  TP = entry +/- (SL distance * R:R)
          - SL missing, TP present:  SL = entry -/+ (TP distance / R:R)
          - Both missing:            TP = entry +/- default_tp_pips, SL from R:R
        """
        has_tp = bool(signal.take_profits)
        has_sl = signal.stop_loss is not None

        if has_tp and has_sl:
            return  # Nothing to fill

        # Determine entry price (prefer signal's, fall back to market)
        entry = signal.get_entry_average()
        if entry is None:
            broker_sym = self.resolve_symbol(signal.symbol) or signal.symbol
            tick = mt5.symbol_info_tick(broker_sym) if MT5_AVAILABLE and self._connected else None
            if tick is None:
                logger.warning(f"Cannot compute SL/TP: no entry price and no market tick for {signal.symbol}")
                return
            entry = tick.ask if signal.direction == 'BUY' else tick.bid

        is_buy = signal.direction == 'BUY'
        rr = self.risk_reward_ratio

        if has_sl and not has_tp:
            # Compute TP1 from SL distance * R:R
            sl_distance = abs(entry - signal.stop_loss)
            tp_distance = sl_distance * rr
            tp1 = entry + tp_distance if is_buy else entry - tp_distance
            signal.take_profits = [round(tp1, 5)]
            logger.info(
                f"Computed TP1={tp1:.5f} from SL distance={sl_distance:.5f} * R:R={rr} "
                f"for {signal.symbol} {signal.direction}"
            )

        elif has_tp and not has_sl:
            # Compute SL from TP1 distance / R:R
            tp1 = signal.take_profits[0]
            tp_distance = abs(tp1 - entry)
            sl_distance = tp_distance / rr
            sl = entry - sl_distance if is_buy else entry + sl_distance
            signal.stop_loss = round(sl, 5)
            logger.info(
                f"Computed SL={sl:.5f} from TP1 distance={tp_distance:.5f} / R:R={rr} "
                f"for {signal.symbol} {signal.direction}"
            )

        else:
            # Both missing - use default_tp_pips then R:R for SL
            pip_size = self._get_pip_size(signal.symbol)
            if pip_size is None:
                logger.warning(f"Cannot compute SL/TP: no pip size available for {signal.symbol}")
                return

            tp_distance = self.default_tp_pips * pip_size
            sl_distance = tp_distance / rr

            tp1 = entry + tp_distance if is_buy else entry - tp_distance
            sl = entry - sl_distance if is_buy else entry + sl_distance

            signal.take_profits = [round(tp1, 5)]
            signal.stop_loss = round(sl, 5)
            logger.info(
                f"Computed TP1={tp1:.5f} ({self.default_tp_pips} pips) and SL={sl:.5f} "
                f"(R:R={rr}) for {signal.symbol} {signal.direction}"
            )

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

    def _get_entry_prices(self, signal: Signal, num_positions: int, symbol: str) -> List[float]:
        """
        Generate evenly distributed entry prices across the entry range.

        For ranged entries (min/max): distributes across that range.
        For single entry: creates a synthetic range of entry_range_pips.
        """
        pip_size = self._get_pip_size(signal.symbol) or self._fallback_pip_size(signal.symbol)

        if signal.entry_price_min is not None and signal.entry_price_max is not None:
            range_min = signal.entry_price_min
            range_max = signal.entry_price_max
        elif signal.entry_price is not None:
            offset = self.entry_range_pips * pip_size
            if signal.direction == 'BUY':
                range_min = signal.entry_price
                range_max = signal.entry_price + offset
            else:
                range_min = signal.entry_price - offset
                range_max = signal.entry_price
        else:
            return []

        if num_positions == 1:
            return [round((range_min + range_max) / 2, 5)]

        step = (range_max - range_min) / (num_positions - 1)
        prices = [round(range_min + i * step, 5) for i in range(num_positions)]
        logger.info(
            f"Entry distribution for {signal.symbol} {signal.direction}: "
            f"range=[{range_min:.5f}, {range_max:.5f}], pip_size={pip_size}, "
            f"prices={prices}"
        )
        return prices

    def _open_positions(self, signal: Signal, num_positions: int, broker_symbol: str = None) -> Optional[List[OpenedPosition]]:
        """Open multiple positions distributed across TPs, using market or limit orders."""
        try:
            symbol = broker_symbol or self.resolve_symbol(signal.symbol) or signal.symbol
            direction = signal.direction
            lot_size = self._compute_lot_size(signal)

            # Ensure symbol is visible in Market Watch before getting tick
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol {symbol}")
                return None

            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get tick for {symbol}")
                return None

            current_price = tick.ask if direction == 'BUY' else tick.bid

            # Determine if we should use limit orders or market orders
            use_limit = False
            if not signal.is_market_order and (
                signal.entry_price is not None
                or (signal.entry_price_min is not None and signal.entry_price_max is not None)
            ):
                # Get the entry zone boundaries
                if signal.entry_price_min is not None and signal.entry_price_max is not None:
                    entry_min = signal.entry_price_min
                    entry_max = signal.entry_price_max
                else:
                    pip_size = self._get_pip_size(signal.symbol) or self._fallback_pip_size(signal.symbol)
                    offset = self.entry_range_pips * pip_size
                    if direction == 'BUY':
                        entry_min = signal.entry_price
                        entry_max = signal.entry_price + offset
                    else:
                        entry_min = signal.entry_price - offset
                        entry_max = signal.entry_price

                # Check if current price is already in/past the entry zone
                if direction == 'BUY':
                    # For BUY: limit if price is above the entry zone (needs to come down)
                    use_limit = current_price > entry_max
                else:
                    # For SELL: limit if price is below the entry zone (needs to come up)
                    use_limit = current_price < entry_min

            # Distribute positions across TPs
            distribution = self._distribute_positions(num_positions, signal.take_profits)

            # Flatten distribution into per-position list of (tp_price, tp_label)
            position_tps = []
            for tp_price, count, tp_label in distribution:
                for _ in range(count):
                    position_tps.append((tp_price, tp_label))

            # Generate entry prices for limit orders
            if use_limit:
                entry_prices = self._get_entry_prices(signal, num_positions, symbol)
                if not entry_prices:
                    use_limit = False

            opened = []
            errors = 0

            for idx, (tp_price, tp_label) in enumerate(position_tps):
                if use_limit:
                    entry_price = entry_prices[idx]

                    # Determine pending order type
                    if direction == 'BUY':
                        if entry_price < current_price:
                            order_type = mt5.ORDER_TYPE_BUY_LIMIT
                        else:
                            order_type = mt5.ORDER_TYPE_BUY_STOP
                    else:
                        if entry_price > current_price:
                            order_type = mt5.ORDER_TYPE_SELL_LIMIT
                        else:
                            order_type = mt5.ORDER_TYPE_SELL_STOP

                    expiry = datetime.now() + timedelta(minutes=self.pending_expiry_minutes)
                    expiry_timestamp = int(expiry.timestamp())

                    request = {
                        "action": mt5.TRADE_ACTION_PENDING,
                        "symbol": symbol,
                        "volume": lot_size,
                        "type": order_type,
                        "price": entry_price,
                        "sl": signal.stop_loss,
                        "tp": tp_price,
                        "magic": self.magic_number,
                        "comment": f"TGS_{signal.message_id}_{tp_label}"[:31],
                        "type_time": mt5.ORDER_TIME_SPECIFIED,
                        "expiration": expiry_timestamp,
                        "type_filling": mt5.ORDER_FILLING_RETURN,
                    }
                    pos_order_type = "pending"
                    pos_price = entry_price
                else:
                    # Market order
                    if direction == 'BUY':
                        order_type = mt5.ORDER_TYPE_BUY
                    else:
                        order_type = mt5.ORDER_TYPE_SELL

                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": lot_size,
                        "type": order_type,
                        "price": current_price,
                        "sl": signal.stop_loss,
                        "tp": tp_price,
                        "deviation": self.slippage,
                        "magic": self.magic_number,
                        "comment": f"TGS_{signal.message_id}_{tp_label}"[:31],
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    pos_order_type = "market"
                    pos_price = current_price

                logger.debug(
                    f"Sending {pos_order_type} order ({tp_label}): "
                    f"price={pos_price}, sl={signal.stop_loss}, tp={tp_price}"
                )

                result = mt5.order_send(request)

                if result is None:
                    error = mt5.last_error()
                    logger.error(f"Order send returned None ({tp_label}): {error}")
                    errors += 1
                    continue

                # Pending orders return TRADE_RETCODE_PLACED, market orders return TRADE_RETCODE_DONE
                success_codes = {mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED}
                if result.retcode not in success_codes:
                    logger.error(
                        f"Order failed ({tp_label}): retcode={result.retcode}, "
                        f"comment={result.comment}, "
                        f"price={pos_price}, sl={signal.stop_loss}, tp={tp_price}"
                    )
                    self._positions.append(OpenedPosition(
                        ticket=0,
                        signal_message_id=signal.message_id,
                        channel_username=signal.channel_username,
                        symbol=symbol,
                        direction=direction,
                        volume=lot_size,
                        open_price=pos_price,
                        stop_loss=signal.stop_loss,
                        take_profit=tp_price,
                        tp_label=tp_label,
                        order_type=pos_order_type,
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
                    open_price=result.price if not use_limit else pos_price,
                    stop_loss=signal.stop_loss,
                    take_profit=tp_price,
                    tp_label=tp_label,
                    order_type=pos_order_type,
                )
                self._positions.append(position)
                opened.append(position)

                # Refresh price for next market order
                if not use_limit:
                    tick = mt5.symbol_info_tick(symbol)
                    if tick:
                        current_price = tick.ask if direction == 'BUY' else tick.bid

            # Log summary
            order_mode = "pending limit" if use_limit else "market"
            tp_summary = ", ".join(
                f"{count}x {label}@{tp}" for tp, count, label in distribution
            )
            if use_limit:
                entry_range = f" entries={entry_prices[0]:.5f}-{entry_prices[-1]:.5f}"
            else:
                entry_range = ""
            logger.info(
                f"Placed {len(opened)}/{num_positions} {order_mode} orders for "
                f"{direction} {symbol} (errors: {errors}): {tp_summary}{entry_range}"
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

    def close_positions(
        self,
        channel_username: str = None,
        direction: str = None,
        symbol: str = None,
    ) -> int:
        """
        Close open positions matching the given filters.

        Args:
            channel_username: Only close positions from this channel (None = all)
            direction: Only close BUY or SELL (None = both)
            symbol: Only close this symbol (None = all)

        Returns:
            Number of positions successfully closed
        """
        if not self._connected or not MT5_AVAILABLE:
            logger.warning("MT5 not connected, cannot close positions")
            return 0

        # Get live positions from MT5 filtered by our magic number
        positions = mt5.positions_get()
        if not positions:
            logger.info("No open positions found in MT5")
            return 0

        our_positions = [p for p in positions if p.magic == self.magic_number]

        # Apply filters
        if symbol:
            broker_sym = self.resolve_symbol(symbol) or symbol
            our_positions = [p for p in our_positions if p.symbol == broker_sym]
        if direction:
            dir_type = 0 if direction == 'BUY' else 1  # MT5: 0=BUY, 1=SELL
            our_positions = [p for p in our_positions if p.type == dir_type]
        if channel_username:
            # Filter by comment tag (TGS_{msg_id}_...)
            # Also match against our internal tracking
            tracked_tickets = {
                pos.ticket for pos in self._positions
                if pos.channel_username == channel_username and pos.status == "open"
            }
            our_positions = [p for p in our_positions if p.ticket in tracked_tickets]

        closed = 0
        for pos in our_positions:
            try:
                # Opposite direction to close
                close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                tick = mt5.symbol_info_tick(pos.symbol)
                if not tick:
                    continue
                close_price = tick.bid if pos.type == 0 else tick.ask

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": close_type,
                    "position": pos.ticket,
                    "price": close_price,
                    "deviation": self.slippage,
                    "magic": self.magic_number,
                    "comment": f"TGS_CLOSE",
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    closed += 1
                    # Update internal tracking
                    for tracked in self._positions:
                        if tracked.ticket == pos.ticket:
                            tracked.status = "closed"
                    logger.info(f"Closed position {pos.ticket} ({pos.symbol})")
                else:
                    comment = result.comment if result else "None"
                    logger.error(f"Failed to close {pos.ticket}: {comment}")
            except Exception as e:
                logger.error(f"Error closing position {pos.ticket}: {e}")

        logger.info(f"Closed {closed}/{len(our_positions)} positions")
        return closed

    def cancel_pending_orders(
        self,
        channel_username: str = None,
        symbol: str = None,
    ) -> int:
        """Cancel pending orders matching filters."""
        if not self._connected or not MT5_AVAILABLE:
            return 0

        orders = mt5.orders_get()
        if not orders:
            return 0

        our_orders = [o for o in orders if o.magic == self.magic_number]

        if symbol:
            broker_sym = self.resolve_symbol(symbol) or symbol
            our_orders = [o for o in our_orders if o.symbol == broker_sym]
        if channel_username:
            tracked_tickets = {
                pos.ticket for pos in self._positions
                if pos.channel_username == channel_username and pos.order_type == "pending"
            }
            our_orders = [o for o in our_orders if o.ticket in tracked_tickets]

        cancelled = 0
        for order in our_orders:
            try:
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": order.ticket,
                }
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    cancelled += 1
                    for tracked in self._positions:
                        if tracked.ticket == order.ticket:
                            tracked.status = "closed"
                    logger.info(f"Cancelled pending order {order.ticket}")
                else:
                    comment = result.comment if result else "None"
                    logger.error(f"Failed to cancel order {order.ticket}: {comment}")
            except Exception as e:
                logger.error(f"Error cancelling order {order.ticket}: {e}")

        logger.info(f"Cancelled {cancelled}/{len(our_orders)} pending orders")
        return cancelled

    def move_sl_to_break_even(
        self,
        channel_username: str = None,
        symbol: str = None,
    ) -> int:
        """
        Move stop loss to entry price (break even) for matching positions.

        Returns:
            Number of positions modified
        """
        if not self._connected or not MT5_AVAILABLE:
            logger.warning("MT5 not connected, cannot modify positions")
            return 0

        positions = mt5.positions_get()
        if not positions:
            return 0

        our_positions = [p for p in positions if p.magic == self.magic_number]

        if symbol:
            broker_sym = self.resolve_symbol(symbol) or symbol
            our_positions = [p for p in our_positions if p.symbol == broker_sym]
        if channel_username:
            tracked_tickets = {
                pos.ticket for pos in self._positions
                if pos.channel_username == channel_username and pos.status == "open"
            }
            our_positions = [p for p in our_positions if p.ticket in tracked_tickets]

        modified = 0
        for pos in our_positions:
            try:
                # Only move SL if position is in profit (SL would improve)
                is_buy = pos.type == 0
                if is_buy and pos.price_open <= pos.sl:
                    continue  # SL already at or above entry
                if not is_buy and pos.sl != 0.0 and pos.price_open >= pos.sl:
                    continue  # SL already at or below entry

                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "symbol": pos.symbol,
                    "sl": pos.price_open,  # Move SL to entry price
                    "tp": pos.tp,          # Keep existing TP
                }

                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    modified += 1
                    # Update internal tracking
                    for tracked in self._positions:
                        if tracked.ticket == pos.ticket:
                            tracked.stop_loss = pos.price_open
                    logger.info(
                        f"Break-even set for {pos.ticket}: SL moved to {pos.price_open}"
                    )
                else:
                    comment = result.comment if result else "None"
                    logger.error(f"Failed to modify {pos.ticket}: {comment}")
            except Exception as e:
                logger.error(f"Error modifying position {pos.ticket}: {e}")

        logger.info(f"Break-even applied to {modified}/{len(our_positions)} positions")
        return modified

    def partial_close_positions(
        self,
        channel_username: str = None,
        symbol: str = None,
    ) -> tuple:
        """
        Close higher-entry positions and move the lowest entry to break even.

        For BUY: keeps the position with the lowest open_price, closes the rest.
        For SELL: keeps the position with the highest open_price, closes the rest.

        Returns:
            (closed_count, be_count) tuple
        """
        if not self._connected or not MT5_AVAILABLE:
            logger.warning("MT5 not connected, cannot partial close")
            return (0, 0)

        positions = mt5.positions_get()
        if not positions:
            return (0, 0)

        our_positions = [p for p in positions if p.magic == self.magic_number]

        if symbol:
            broker_sym = self.resolve_symbol(symbol) or symbol
            our_positions = [p for p in our_positions if p.symbol == broker_sym]
        if channel_username:
            tracked_tickets = {
                pos.ticket for pos in self._positions
                if pos.channel_username == channel_username and pos.status == "open"
            }
            our_positions = [p for p in our_positions if p.ticket in tracked_tickets]

        if len(our_positions) <= 1:
            # Only 1 or 0 positions — just apply BE
            be_count = self.move_sl_to_break_even(channel_username, symbol)
            return (0, be_count)

        # Group by direction (BUY=0, SELL=1)
        buys = [p for p in our_positions if p.type == 0]
        sells = [p for p in our_positions if p.type == 1]

        to_close = []
        to_be = []

        # For BUY: keep lowest entry (best price), close higher
        if buys:
            buys_sorted = sorted(buys, key=lambda p: p.price_open)
            to_be.append(buys_sorted[0])       # Keep lowest
            to_close.extend(buys_sorted[1:])   # Close higher entries

        # For SELL: keep highest entry (best price), close lower
        if sells:
            sells_sorted = sorted(sells, key=lambda p: p.price_open, reverse=True)
            to_be.append(sells_sorted[0])       # Keep highest
            to_close.extend(sells_sorted[1:])   # Close lower entries

        # Close the higher-entry positions
        closed = 0
        for pos in to_close:
            try:
                close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                tick = mt5.symbol_info_tick(pos.symbol)
                if not tick:
                    continue
                close_price = tick.bid if pos.type == 0 else tick.ask

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": close_type,
                    "position": pos.ticket,
                    "price": close_price,
                    "deviation": self.slippage,
                    "magic": self.magic_number,
                    "comment": "TGS_PARTIAL",
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    closed += 1
                    for tracked in self._positions:
                        if tracked.ticket == pos.ticket:
                            tracked.status = "closed"
                    logger.info(f"Partial close: closed {pos.ticket} (entry {pos.price_open})")
                else:
                    comment = result.comment if result else "None"
                    logger.error(f"Failed to close {pos.ticket}: {comment}")
            except Exception as e:
                logger.error(f"Error closing position {pos.ticket}: {e}")

        # Move remaining to break even
        be_applied = 0
        for pos in to_be:
            try:
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "symbol": pos.symbol,
                    "sl": pos.price_open,
                    "tp": pos.tp,
                }
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    be_applied += 1
                    for tracked in self._positions:
                        if tracked.ticket == pos.ticket:
                            tracked.stop_loss = pos.price_open
                    logger.info(f"BE set on kept position {pos.ticket} (entry {pos.price_open})")
                else:
                    comment = result.comment if result else "None"
                    logger.error(f"Failed to set BE on {pos.ticket}: {comment}")
            except Exception as e:
                logger.error(f"Error setting BE on {pos.ticket}: {e}")

        logger.info(
            f"Partial close: closed {closed}/{len(to_close)}, "
            f"BE on {be_applied}/{len(to_be)} kept positions"
        )
        return (closed, be_applied)

    @property
    def is_connected(self) -> bool:
        return self._connected
