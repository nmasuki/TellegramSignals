"""Signal validation logic"""
import logging
import math
from typing import List, Tuple, Optional

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
            'XAUUSD', 'XAGUSD', 'EURUSD', 'GBPUSD', 'BTCUSD',
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

        # Check for typos/mistakes in values
        self._detect_typos(signal)

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

    def _detect_typos(self, signal: Signal):
        """
        Detect potential typos in signal values.

        Checks for:
        - TP values with wrong magnitude (extra/missing digits)
        - Values that break expected progression pattern
        - SL values that seem mistyped

        Args:
            signal: Signal to check

        Raises:
            ValueError: If likely typo detected
        """
        entry_price = signal.get_entry_average()
        if entry_price is None:
            return

        warnings = []

        # Check TPs for magnitude errors
        if signal.take_profits and len(signal.take_profits) >= 2:
            tp_warnings = self._check_tp_magnitude(signal.take_profits, entry_price)
            warnings.extend(tp_warnings)

        # Check SL for magnitude errors
        if signal.stop_loss:
            sl_warning = self._check_sl_magnitude(signal.stop_loss, entry_price)
            if sl_warning:
                warnings.append(sl_warning)

        # If any warnings, raise with all detected issues
        if warnings:
            raise ValueError("Possible typo detected: " + "; ".join(warnings))

    def _check_tp_magnitude(self, take_profits: List[float], entry_price: float) -> List[str]:
        """
        Check TPs for magnitude errors (extra/missing digits).

        Args:
            take_profits: List of TP values
            entry_price: Entry price for reference

        Returns:
            List of warning messages
        """
        warnings = []

        # Get the expected number of digits based on entry price
        entry_digits = self._count_significant_digits(entry_price)

        for i, tp in enumerate(take_profits, 1):
            tp_digits = self._count_significant_digits(tp)

            # Check if TP has significantly different magnitude
            if abs(tp_digits - entry_digits) >= 1:
                # Calculate ratio to entry
                ratio = tp / entry_price if entry_price else 0

                # If ratio suggests wrong magnitude (10x or 0.1x off)
                if ratio > 5 or ratio < 0.2:
                    # Try to detect if it's an extra/missing digit
                    corrected = self._suggest_correction(tp, entry_price, take_profits, i)
                    if corrected:
                        warnings.append(
                            f"TP{i} ({tp}) looks wrong - did you mean {corrected}? "
                            f"(possible extra/missing digit)"
                        )
                    else:
                        warnings.append(
                            f"TP{i} ({tp}) has unusual magnitude vs entry ({entry_price})"
                        )

        # Check for outliers in TP progression
        progression_warnings = self._check_tp_progression(take_profits, entry_price)
        warnings.extend(progression_warnings)

        return warnings

    def _check_tp_progression(self, take_profits: List[float], entry_price: float) -> List[str]:
        """
        Check if any TP breaks the expected progression pattern.

        For a SELL with TPs at 78100, 78000, 77900, 75000, the spacing should be consistent
        (or gradually increasing). A value like 779000 would be a clear outlier.
        """
        warnings = []

        if len(take_profits) < 3:
            return warnings

        # Calculate distances from entry
        distances = [abs(tp - entry_price) for tp in take_profits]

        # Calculate median distance
        sorted_distances = sorted(distances)
        median_distance = sorted_distances[len(sorted_distances) // 2]

        # Check each TP for outliers (more than 10x the median distance)
        for i, (tp, dist) in enumerate(zip(take_profits, distances), 1):
            if median_distance > 0 and dist > median_distance * 10:
                warnings.append(
                    f"TP{i} ({tp}) is an outlier - distance from entry "
                    f"({dist:.0f}) is >10x median ({median_distance:.0f})"
                )

        return warnings

    def _check_sl_magnitude(self, stop_loss: float, entry_price: float) -> Optional[str]:
        """
        Check SL for magnitude errors.

        Args:
            stop_loss: Stop loss value
            entry_price: Entry price for reference

        Returns:
            Warning message if issue detected, None otherwise
        """
        ratio = stop_loss / entry_price if entry_price else 0

        # SL should typically be within 10% of entry for most instruments
        # But crypto can have wider stops, so check for 10x magnitude errors
        if ratio > 5 or ratio < 0.2:
            return f"SL ({stop_loss}) has unusual magnitude vs entry ({entry_price})"

        return None

    def _count_significant_digits(self, value: float) -> int:
        """Count the number of digits in the integer part of a value."""
        if value <= 0:
            return 0
        return int(math.log10(value)) + 1

    def _suggest_correction(
        self,
        value: float,
        entry_price: float,
        other_values: List[float],
        index: int
    ) -> Optional[float]:
        """
        Try to suggest a corrected value for a suspected typo.

        Args:
            value: The potentially wrong value
            entry_price: Entry price for reference
            other_values: Other TP values for context
            index: 1-based index of the value

        Returns:
            Suggested corrected value, or None if can't determine
        """
        # Get valid other values (exclude the problematic one)
        valid_others = [v for i, v in enumerate(other_values, 1) if i != index]

        # Try multiplying/dividing by 10 to see if it makes sense
        candidates = []
        for factor in [10, 100, 0.1, 0.01]:
            if factor > 1:
                corrected = value * factor  # Missing digit - multiply to add zeros
            else:
                corrected = value / abs(1/factor)  # Extra digit - divide to remove zeros

            # Check if corrected value is close to entry magnitude
            ratio = corrected / entry_price if entry_price else 0
            if 0.5 < ratio < 2:
                # Calculate how well it fits with other TPs
                if valid_others:
                    # Check if it fits the progression pattern
                    avg_other = sum(valid_others) / len(valid_others)
                    avg_distance = sum(abs(v - entry_price) for v in valid_others) / len(valid_others)
                    corrected_distance = abs(corrected - entry_price)

                    # Score based on how well it fits
                    distance_ratio = corrected_distance / avg_distance if avg_distance else float('inf')

                    # Good if distance is within 5x of average
                    if distance_ratio < 5:
                        candidates.append((corrected, distance_ratio))

        # Return the best candidate (closest to average distance pattern)
        if candidates:
            best = min(candidates, key=lambda x: x[1])
            return round(best[0], 2)

        return None
