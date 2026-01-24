"""Signal validation logic"""
import logging
from typing import List

from .models import Signal


logger = logging.getLogger(__name__)


class SignalValidator:
    """Validates extracted trading signals"""

    def __init__(self, allowed_symbols: List[str] = None):
        """
        Initialize validator

        Args:
            allowed_symbols: List of allowed symbol names (optional)
        """
        self.allowed_symbols = allowed_symbols or [
            'XAUUSD', 'EURUSD', 'GBPUSD', 'BTCUSD',
            'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'USDCHF'
        ]

    def validate_signal(self, signal: Signal) -> bool:
        """
        Validate a signal

        Args:
            signal: Signal to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        self._validate_required_fields(signal)

        # Validate symbol
        if self.allowed_symbols:
            self._validate_symbol(signal)

        # Validate price logic
        self._validate_price_logic(signal)

        # Validate entry range
        self._validate_entry_range(signal)

        logger.debug(f"Signal validation passed for {signal.symbol} {signal.direction}")
        return True

    def _validate_required_fields(self, signal: Signal):
        """Validate that required fields are present"""
        if not signal.symbol:
            raise ValueError("Missing required field: symbol")

        if not signal.direction:
            raise ValueError("Missing required field: direction")

        if signal.direction not in ['BUY', 'SELL']:
            raise ValueError(f"Invalid direction: {signal.direction}")

        if not signal.has_entry():
            raise ValueError("Missing entry price information")

    def _validate_symbol(self, signal: Signal):
        """Validate symbol against allowed list"""
        if signal.symbol not in self.allowed_symbols:
            logger.warning(f"Symbol {signal.symbol} not in allowed list")
            # Don't raise error, just warn

    def _validate_price_logic(self, signal: Signal):
        """Validate that prices make sense relative to each other"""
        entry_price = signal.get_entry_average()

        if entry_price is None:
            return  # Can't validate without entry price

        # Validate stop loss logic
        if signal.stop_loss:
            if signal.direction == "BUY":
                if signal.stop_loss >= entry_price:
                    raise ValueError(
                        f"BUY signal: Stop loss ({signal.stop_loss}) should be below "
                        f"entry ({entry_price})"
                    )
            elif signal.direction == "SELL":
                if signal.stop_loss <= entry_price:
                    raise ValueError(
                        f"SELL signal: Stop loss ({signal.stop_loss}) should be above "
                        f"entry ({entry_price})"
                    )

        # Validate take profit logic
        if signal.take_profits:
            for i, tp in enumerate(signal.take_profits, 1):
                if signal.direction == "BUY":
                    if tp <= entry_price:
                        raise ValueError(
                            f"BUY signal: TP{i} ({tp}) should be above entry ({entry_price})"
                        )
                elif signal.direction == "SELL":
                    if tp >= entry_price:
                        raise ValueError(
                            f"SELL signal: TP{i} ({tp}) should be below entry ({entry_price})"
                        )

            # Validate TP ordering (optional - TPs should increase for BUY, decrease for SELL)
            for i in range(len(signal.take_profits) - 1):
                tp1 = signal.take_profits[i]
                tp2 = signal.take_profits[i + 1]

                if signal.direction == "BUY" and tp2 <= tp1:
                    logger.warning(f"BUY signal: TP ordering unusual (TP{i+1}={tp1}, TP{i+2}={tp2})")
                elif signal.direction == "SELL" and tp2 >= tp1:
                    logger.warning(f"SELL signal: TP ordering unusual (TP{i+1}={tp1}, TP{i+2}={tp2})")

    def _validate_entry_range(self, signal: Signal):
        """Validate entry range if present"""
        if signal.entry_price_min and signal.entry_price_max:
            if signal.entry_price_min >= signal.entry_price_max:
                raise ValueError(
                    f"Entry min ({signal.entry_price_min}) should be less than "
                    f"max ({signal.entry_price_max})"
                )
