"""Signal extractor - coordinates pattern matching and validation"""
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any

from .models import Signal, ExtractionError
from .patterns import PatternMatcher
from .validators import SignalValidator


logger = logging.getLogger(__name__)


class SignalExtractor:
    """Extracts trading signals from text messages"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize signal extractor

        Args:
            config: Extraction configuration dictionary
        """
        self.config = config
        self.min_confidence = config.get('min_confidence', 0.75)

        # Initialize components
        symbol_mapping = config.get('symbol_mapping', {})
        self.pattern_matcher = PatternMatcher(symbol_mapping)
        self.validator = SignalValidator()

        # Confidence weights
        self.confidence_weights = config.get('confidence_weights', {
            'symbol': 0.25,
            'direction': 0.25,
            'entry': 0.20,
            'stop_loss': 0.15,
            'take_profit': 0.15
        })

        # Channel confidence multipliers (from research on channel reliability)
        self.channel_confidence = config.get('channel_confidence', {})

        logger.info(f"Signal extractor initialized (min_confidence: {self.min_confidence})")

    def is_signal(self, text: str) -> bool:
        """
        Quick check if message is likely a signal

        Args:
            text: Message text

        Returns:
            True if message contains signal keywords
        """
        return self.pattern_matcher.is_signal(text)

    def extract_signal(
        self,
        text: str,
        message_id: int,
        channel_username: str,
        timestamp: datetime
    ) -> Signal:
        """
        Extract signal from message text

        Args:
            text: Message text
            message_id: Telegram message ID
            channel_username: Channel username
            timestamp: Message timestamp

        Returns:
            Extracted Signal object

        Raises:
            ValueError: If extraction fails or confidence too low
        """
        logger.debug(f"Extracting signal from message {message_id} (@{channel_username})")

        # Extract all fields
        extracted_fields = {}

        # Symbol
        symbol = self.pattern_matcher.extract_symbol(text)
        extracted_fields['symbol'] = symbol

        # Direction
        direction = self.pattern_matcher.extract_direction(text)
        extracted_fields['direction'] = direction

        # Entry
        entry_single, entry_min, entry_max = self.pattern_matcher.extract_entry(text)
        extracted_fields['entry_price'] = entry_single
        extracted_fields['entry_price_min'] = entry_min
        extracted_fields['entry_price_max'] = entry_max

        # Check for "now" keyword indicating immediate market execution
        is_market_order = bool(re.search(r'\bnow\b', text, re.IGNORECASE))
        extracted_fields['is_market_order'] = is_market_order

        # Stop Loss - try pips format first, then absolute values
        stop_loss = None
        sl_pips = self.pattern_matcher.extract_stop_loss_pips(text)
        if sl_pips:
            # Calculate SL price from pips
            entry_ref = entry_single or ((entry_min + entry_max) / 2 if entry_min and entry_max else None)
            if entry_ref and direction:
                stop_loss = self._calculate_sl_from_pips(entry_ref, direction, sl_pips, symbol)
                logger.debug(f"Calculated SL from pips: {stop_loss} ({sl_pips} pips)")
        else:
            # Try absolute SL value
            stop_loss = self.pattern_matcher.extract_stop_loss(text)

        extracted_fields['stop_loss'] = stop_loss
        extracted_fields['sl_pips'] = sl_pips

        # Take Profits - try pips formats first, then absolute values
        take_profits = []
        entry_ref = entry_single or ((entry_min + entry_max) / 2 if entry_min and entry_max else None)

        # Try numbered pips format first (tp1 3pips, tp2 4pips, etc.)
        tp_pips_numbered = self.pattern_matcher.extract_take_profits_pips_numbered(text)
        if tp_pips_numbered and entry_ref and direction:
            # Calculate TP prices from numbered pips list
            take_profits = self._calculate_tp_from_pips_list(
                entry_ref, direction, tp_pips_numbered, symbol
            )
            logger.debug(f"Calculated TPs from numbered pips: {take_profits} ({tp_pips_numbered})")
        else:
            # Try range pips format (TP 30-100pips)
            tp_pips = self.pattern_matcher.extract_take_profits_pips(text)
            if tp_pips:
                # Calculate TP prices from pips range
                if entry_ref and direction:
                    take_profits = self._calculate_tp_from_pips(
                        entry_ref, direction, tp_pips, symbol
                    )
                    logger.debug(f"Calculated TPs from pips: {take_profits} ({tp_pips} pips)")
            else:
                # Try absolute TP values
                tp_list = self.pattern_matcher.extract_take_profits(text)
                take_profits = [tp_price for _, tp_price in tp_list]

        # Resolve truncated prices (e.g., "90" instead of "5190")
        entry_single, entry_min, entry_max, stop_loss, take_profits = self._resolve_truncated_prices(
            symbol=symbol,
            entry_single=entry_single,
            entry_min=entry_min,
            entry_max=entry_max,
            stop_loss=stop_loss,
            take_profits=take_profits,
        )
        extracted_fields['entry_price'] = entry_single
        extracted_fields['entry_price_min'] = entry_min
        extracted_fields['entry_price_max'] = entry_max
        extracted_fields['stop_loss'] = stop_loss

        # Auto-correct typos in TP values
        entry_ref = entry_single or ((entry_min + entry_max) / 2 if entry_min and entry_max else None)
        if entry_ref and take_profits:
            take_profits, tp_corrections = self._auto_correct_typos(take_profits, entry_ref)
            if tp_corrections:
                logger.info(f"Auto-corrected TPs: {tp_corrections}")

        extracted_fields['take_profits'] = take_profits

        # Calculate confidence score (includes channel confidence as weighted component)
        confidence = self._calculate_confidence(extracted_fields, channel_username)

        # Log channel confidence impact
        channel_conf = self.channel_confidence.get(channel_username, 1.0)
        if channel_conf != 1.0:
            logger.debug(f"Channel @{channel_username} confidence: {channel_conf:.2f}")

        # Validate and potentially correct signal setup (direction vs TP/SL logic)
        direction, confidence, setup_notes = self._validate_and_correct_setup(
            direction=direction,
            entry_single=entry_single,
            entry_min=entry_min,
            entry_max=entry_max,
            stop_loss=stop_loss,
            take_profits=take_profits,
            confidence=confidence
        )
        extracted_fields['direction'] = direction  # Update in case it was corrected

        # Create signal object
        signal = Signal(
            message_id=message_id,
            channel_username=channel_username,
            timestamp=timestamp,
            symbol=symbol or "",
            direction=direction or "",
            entry_price=entry_single,
            entry_price_min=entry_min,
            entry_price_max=entry_max,
            stop_loss=stop_loss,
            take_profits=take_profits,
            confidence_score=confidence,
            raw_message=text
        )

        # Add setup validation notes
        if setup_notes:
            signal.extraction_notes = setup_notes

        # Validate signal
        try:
            self.validator.validate_signal(signal)
        except ValueError as e:
            logger.warning(f"Signal validation failed: {e}")
            if signal.extraction_notes:
                signal.extraction_notes += f"; Validation warning: {e}"
            else:
                signal.extraction_notes = f"Validation warning: {e}"

        # Check confidence threshold
        if confidence < self.min_confidence:
            raise ValueError(
                f"Confidence score ({confidence:.2f}) below threshold ({self.min_confidence})"
            )

        logger.info(
            f"Extracted signal: {signal.symbol} {signal.direction} "
            f"(confidence: {confidence:.2f})"
        )

        return signal

    def _get_pip_value(self, symbol: str) -> float:
        """
        Get pip value for a symbol

        Args:
            symbol: Trading symbol (e.g., XAUUSD, EURUSD)

        Returns:
            Pip value in price terms
        """
        # Gold/XAUUSD: 1 pip = 1.0 (common for signal providers)
        if symbol in ('XAUUSD', 'GOLD'):
            return 1.0
        # Silver/XAGUSD: 1 pip = 0.01
        if symbol in ('XAGUSD', 'SILVER'):
            return 0.01
        # JPY pairs: 1 pip = 0.01
        if 'JPY' in symbol:
            return 0.01
        # Standard forex pairs: 1 pip = 0.0001
        return 0.0001

    def _calculate_tp_from_pips(
        self,
        entry_price: float,
        direction: str,
        tp_pips: tuple,
        symbol: str
    ) -> list:
        """
        Calculate TP prices from pips

        Args:
            entry_price: Entry price for the trade
            direction: "BUY" or "SELL"
            tp_pips: Tuple of (min_pips, max_pips) or (pips, None)
            symbol: Trading symbol

        Returns:
            List of calculated TP prices
        """
        pip_value = self._get_pip_value(symbol or 'XAUUSD')
        min_pips, max_pips = tp_pips

        take_profits = []

        if direction == 'BUY':
            # BUY: TPs are above entry
            take_profits.append(round(entry_price + min_pips * pip_value, 2))
            if max_pips:
                take_profits.append(round(entry_price + max_pips * pip_value, 2))
        else:
            # SELL: TPs are below entry
            take_profits.append(round(entry_price - min_pips * pip_value, 2))
            if max_pips:
                take_profits.append(round(entry_price - max_pips * pip_value, 2))

        return take_profits

    def _calculate_tp_from_pips_list(
        self,
        entry_price: float,
        direction: str,
        tp_pips_list: list,
        symbol: str
    ) -> list:
        """
        Calculate TP prices from a list of numbered pips values

        Args:
            entry_price: Entry price for the trade
            direction: "BUY" or "SELL"
            tp_pips_list: List of tuples (tp_number, pips)
            symbol: Trading symbol

        Returns:
            List of calculated TP prices (sorted by TP number)
        """
        pip_value = self._get_pip_value(symbol or 'XAUUSD')
        take_profits = []

        for _, pips in tp_pips_list:
            if direction == 'BUY':
                # BUY: TPs are above entry
                tp_price = round(entry_price + pips * pip_value, 2)
            else:
                # SELL: TPs are below entry
                tp_price = round(entry_price - pips * pip_value, 2)
            take_profits.append(tp_price)

        return take_profits

    def _calculate_sl_from_pips(
        self,
        entry_price: float,
        direction: str,
        sl_pips: int,
        symbol: str
    ) -> float:
        """
        Calculate SL price from pips

        Args:
            entry_price: Entry price for the trade
            direction: "BUY" or "SELL"
            sl_pips: Stop loss in pips
            symbol: Trading symbol

        Returns:
            Calculated SL price
        """
        pip_value = self._get_pip_value(symbol or 'XAUUSD')

        if direction == 'BUY':
            # BUY: SL is below entry
            return round(entry_price - sl_pips * pip_value, 2)
        else:
            # SELL: SL is above entry
            return round(entry_price + sl_pips * pip_value, 2)

    def _calculate_confidence(self, extracted_fields: Dict[str, Any], channel_username: str = None) -> float:
        """
        Calculate confidence score for extracted fields

        Args:
            extracted_fields: Dictionary of extracted fields
            channel_username: Channel username for channel confidence weight

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.0

        # Symbol
        if extracted_fields.get('symbol'):
            score += self.confidence_weights.get('symbol', 0.20)

        # Direction
        if extracted_fields.get('direction'):
            score += self.confidence_weights.get('direction', 0.20)

        # Entry (single or range, or "now" = market order)
        if extracted_fields.get('entry_price') or (
            extracted_fields.get('entry_price_min') and
            extracted_fields.get('entry_price_max')
        ) or extracted_fields.get('is_market_order'):
            # "now" signals get full entry confidence (market execution)
            score += self.confidence_weights.get('entry', 0.15)

        # Stop Loss
        if extracted_fields.get('stop_loss'):
            score += self.confidence_weights.get('stop_loss', 0.15)

        # Take Profits
        take_profits = extracted_fields.get('take_profits', [])
        if take_profits:
            # Full score if 2+ TPs, partial if only 1
            tp_score = self.confidence_weights.get('take_profit', 0.10)
            if len(take_profits) >= 2:
                score += tp_score
            else:
                score += tp_score * 0.5

        # Channel confidence (weighted component based on channel reliability)
        channel_weight = self.confidence_weights.get('channel_confidence', 0.0)
        if channel_weight > 0 and channel_username:
            channel_conf = self.channel_confidence.get(channel_username, 1.0)
            score += channel_weight * channel_conf

        return round(score, 2)

    def _validate_and_correct_setup(
        self,
        direction: str,
        entry_single: float,
        entry_min: float,
        entry_max: float,
        stop_loss: float,
        take_profits: list,
        confidence: float
    ) -> tuple:
        """
        Validate signal setup logic and correct if possible.

        Rules:
        - BUY: TPs should be ABOVE entry, SL should be BELOW entry
        - SELL: TPs should be BELOW entry, SL should be ABOVE entry

        If direction seems wrong but fixable: flip direction, reduce confidence by 30%
        If contradictory and unfixable: set confidence to 0

        Args:
            direction: Extracted direction (BUY/SELL)
            entry_single: Single entry price (or None)
            entry_min: Entry range min
            entry_max: Entry range max
            stop_loss: Stop loss price
            take_profits: List of take profit prices
            confidence: Current confidence score

        Returns:
            Tuple of (corrected_direction, adjusted_confidence, notes)
        """
        notes = ""

        # Need direction and some reference points to validate
        if not direction:
            return direction, confidence, notes

        # Get entry reference price
        if entry_single:
            entry_ref = entry_single
        elif entry_min and entry_max:
            entry_ref = (entry_min + entry_max) / 2
        else:
            # No entry to validate against
            return direction, confidence, notes

        # Analyze TP positions relative to entry
        tps_above = 0
        tps_below = 0
        valid_tps = [tp for tp in take_profits if tp and tp > 0]

        for tp in valid_tps:
            if tp > entry_ref:
                tps_above += 1
            elif tp < entry_ref:
                tps_below += 1

        # Analyze SL position relative to entry
        sl_above = stop_loss and stop_loss > entry_ref
        sl_below = stop_loss and stop_loss < entry_ref

        # Determine expected setup based on direction
        if direction == 'BUY':
            # BUY expects: TPs above entry, SL below entry
            tps_correct = tps_above > tps_below

            if not tps_correct and valid_tps:
                # TPs are mostly below entry - wrong for BUY
                if tps_below > 0 and tps_above == 0:
                    # All TPs below - likely should be SELL
                    if sl_above or not stop_loss:
                        # SL confirms it should be SELL (SL above) or no SL to contradict
                        direction = 'SELL'
                        confidence = max(0, confidence - 0.30)
                        notes = f"Direction corrected BUY->SELL (TPs below entry), confidence reduced 30%"
                        logger.warning(notes)
                    else:
                        # SL below but TPs below too - contradictory
                        confidence = 0
                        notes = f"Contradictory setup: BUY with TPs below entry AND SL below entry"
                        logger.warning(notes)
                elif tps_above > 0 and tps_below > 0:
                    # Mixed TPs - contradictory, can't determine intent
                    confidence = 0
                    notes = f"Contradictory setup: TPs both above and below entry"
                    logger.warning(notes)

        elif direction == 'SELL':
            # SELL expects: TPs below entry, SL above entry
            tps_correct = tps_below > tps_above

            if not tps_correct and valid_tps:
                # TPs are mostly above entry - wrong for SELL
                if tps_above > 0 and tps_below == 0:
                    # All TPs above - likely should be BUY
                    if sl_below or not stop_loss:
                        # SL confirms it should be BUY (SL below) or no SL to contradict
                        direction = 'BUY'
                        confidence = max(0, confidence - 0.30)
                        notes = f"Direction corrected SELL->BUY (TPs above entry), confidence reduced 30%"
                        logger.warning(notes)
                    else:
                        # SL above but TPs above too - contradictory
                        confidence = 0
                        notes = f"Contradictory setup: SELL with TPs above entry AND SL above entry"
                        logger.warning(notes)
                elif tps_above > 0 and tps_below > 0:
                    # Mixed TPs - contradictory, can't determine intent
                    confidence = 0
                    notes = f"Contradictory setup: TPs both above and below entry"
                    logger.warning(notes)

        return direction, round(confidence, 2), notes

    # Typical price ranges per symbol (approximate, used as fallback for truncated price detection)
    SYMBOL_PRICE_RANGES = {
        'XAUUSD': (1800, 10000),
        'XAGUSD': (15, 100),
        'EURUSD': (0.8, 1.5),
        'GBPUSD': (1.0, 2.0),
        'USDJPY': (100, 200),
        'BTCUSD': (10000, 200000),
        'AUDUSD': (0.5, 1.0),
        'USDCAD': (1.0, 1.6),
        'NZDUSD': (0.5, 0.9),
        'USDCHF': (0.8, 1.2),
    }

    def _resolve_truncated_prices(
        self,
        symbol: str,
        entry_single: float,
        entry_min: float,
        entry_max: float,
        stop_loss: float,
        take_profits: list,
    ) -> tuple:
        """
        Resolve truncated prices where only the last few digits are given.

        For example, if XAUUSD is around 3200 and signal says "buy 90",
        the actual entry is likely 3190 or 3290. Uses other prices in the
        signal or the symbol's typical range as reference.

        Returns:
            Tuple of (entry_single, entry_min, entry_max, stop_loss, take_profits)
        """
        # Collect all non-None prices to find a "full" reference
        all_prices = []
        if entry_single:
            all_prices.append(entry_single)
        if entry_min:
            all_prices.append(entry_min)
        if entry_max:
            all_prices.append(entry_max)
        if stop_loss:
            all_prices.append(stop_loss)
        for tp in (take_profits or []):
            if tp:
                all_prices.append(tp)

        if not all_prices:
            return entry_single, entry_min, entry_max, stop_loss, take_profits

        # Determine expected magnitude from symbol
        expected_min, expected_max = self.SYMBOL_PRICE_RANGES.get(
            symbol or '', (0, 0)
        )
        if expected_min == 0:
            return entry_single, entry_min, entry_max, stop_loss, take_profits

        # Find a "full" reference price (one that's within expected range)
        reference = None
        for p in all_prices:
            if expected_min * 0.5 <= p <= expected_max * 2:
                reference = p
                break

        # If no full reference found, use midpoint of expected range
        if reference is None:
            reference = (expected_min + expected_max) / 2
            # Only proceed if ALL prices look truncated
            if any(expected_min * 0.5 <= p <= expected_max * 2 for p in all_prices):
                return entry_single, entry_min, entry_max, stop_loss, take_profits

        def resolve(price):
            if price is None:
                return None
            if expected_min * 0.5 <= price <= expected_max * 2:
                return price  # Already full price
            if price >= expected_max * 2:
                return price  # Too high to be truncated, leave as-is
            return self._expand_truncated(price, reference)

        new_entry_single = resolve(entry_single)
        new_entry_min = resolve(entry_min)
        new_entry_max = resolve(entry_max)
        new_stop_loss = resolve(stop_loss)
        new_take_profits = [resolve(tp) for tp in (take_profits or [])]

        # Log corrections
        corrections = []
        if new_entry_single != entry_single and entry_single is not None:
            corrections.append(f"entry: {entry_single} -> {new_entry_single}")
        if new_entry_min != entry_min and entry_min is not None:
            corrections.append(f"entry_min: {entry_min} -> {new_entry_min}")
        if new_entry_max != entry_max and entry_max is not None:
            corrections.append(f"entry_max: {entry_max} -> {new_entry_max}")
        if new_stop_loss != stop_loss and stop_loss is not None:
            corrections.append(f"SL: {stop_loss} -> {new_stop_loss}")
        for i, (old, new) in enumerate(zip(take_profits or [], new_take_profits)):
            if old != new and old is not None:
                corrections.append(f"TP{i+1}: {old} -> {new}")

        if corrections:
            logger.info(f"Resolved truncated prices: {', '.join(corrections)}")

        return new_entry_single, new_entry_min, new_entry_max, new_stop_loss, new_take_profits

    @staticmethod
    def _expand_truncated(truncated: float, reference: float) -> float:
        """
        Expand a truncated price using a reference price.

        E.g., truncated=90, reference=3190 -> 3190 (or 3090, 3290)
        Picks the candidate closest to the reference.

        Args:
            truncated: The truncated price (e.g., 90)
            reference: A full reference price (e.g., 3190)

        Returns:
            The expanded price
        """
        import math

        if truncated <= 0 or reference <= 0:
            return truncated

        trunc_digits = len(str(int(truncated)))
        ref_digits = len(str(int(reference)))

        if trunc_digits >= ref_digits:
            return truncated  # Not actually truncated

        # The truncated value represents the last N digits
        # e.g., truncated=90, reference=3190
        # We want to try: 3090, 3190, 3290 and pick closest to reference
        modulus = 10 ** trunc_digits  # e.g., 100
        prefix = int(reference) // modulus  # e.g., 31

        candidates = []
        for offset in [-1, 0, 1]:
            candidate_prefix = prefix + offset
            if candidate_prefix < 0:
                continue
            candidate = candidate_prefix * modulus + int(truncated)
            # Preserve decimal part if any
            decimal_part = truncated - int(truncated)
            candidate = float(candidate) + decimal_part
            candidates.append(candidate)

        # Pick closest to reference
        best = min(candidates, key=lambda c: abs(c - reference))
        return round(best, 2)

    def _auto_correct_typos(
        self,
        take_profits: list,
        entry_price: float
    ) -> tuple:
        """
        Auto-correct typos in TP values (extra/missing digits).

        Args:
            take_profits: List of TP prices
            entry_price: Entry price for reference

        Returns:
            Tuple of (corrected_tps, corrections_made)
            corrections_made is a list of strings describing corrections
        """
        import math

        if len(take_profits) < 2:
            return take_profits, []

        corrected = list(take_profits)
        corrections = []

        # Get expected digit count from entry
        entry_digits = int(math.log10(entry_price)) + 1 if entry_price > 0 else 0

        for i, tp in enumerate(take_profits):
            if tp <= 0:
                continue

            tp_digits = int(math.log10(tp)) + 1

            # Check if magnitude is wrong (different digit count)
            if abs(tp_digits - entry_digits) >= 1:
                ratio = tp / entry_price

                # If clearly wrong magnitude (10x or 0.1x off)
                if ratio > 5 or ratio < 0.2:
                    # Try to find correction
                    best_correction = self._find_best_correction(
                        tp, entry_price, take_profits, i
                    )
                    if best_correction:
                        corrected[i] = best_correction
                        corrections.append(f"TP{i+1}: {tp} -> {best_correction}")

        return corrected, corrections

    def _find_best_correction(
        self,
        value: float,
        entry_price: float,
        all_values: list,
        index: int
    ) -> float:
        """
        Find the best correction for a mistyped value.

        Args:
            value: The potentially wrong value
            entry_price: Entry price for reference
            all_values: All TP values for context
            index: Index of the value being corrected

        Returns:
            Corrected value, or None if can't determine
        """
        # Get other values for reference
        others = [v for i, v in enumerate(all_values) if i != index and v > 0]

        candidates = []

        # Try multiplying/dividing by powers of 10
        for factor in [10, 100, 0.1, 0.01]:
            if factor >= 1:
                corrected = value * factor  # Missing digit
            else:
                corrected = value / (1 / factor)  # Extra digit

            # Check if corrected value has right magnitude
            ratio = corrected / entry_price if entry_price else 0
            if 0.5 < ratio < 2:
                # Score by how well it fits with other TPs
                if others:
                    avg_distance = sum(abs(v - entry_price) for v in others) / len(others)
                    corrected_distance = abs(corrected - entry_price)
                    score = abs(corrected_distance - avg_distance) / avg_distance if avg_distance else float('inf')
                    candidates.append((corrected, score))
                else:
                    candidates.append((corrected, abs(ratio - 1)))

        if candidates:
            best = min(candidates, key=lambda x: x[1])
            return round(best[0], 2)

        return None

    def create_extraction_error(
        self,
        text: str,
        message_id: int,
        channel_username: str,
        timestamp: datetime,
        error_reason: str
    ) -> ExtractionError:
        """
        Create an ExtractionError object for a failed extraction

        Args:
            text: Message text
            message_id: Telegram message ID
            channel_username: Channel username
            timestamp: Message timestamp
            error_reason: Reason for extraction failure

        Returns:
            ExtractionError object
        """
        # Try to extract whatever we can for debugging
        extracted_fields = {}
        try:
            extracted_fields['symbol'] = self.pattern_matcher.extract_symbol(text)
            extracted_fields['direction'] = self.pattern_matcher.extract_direction(text)
            entry = self.pattern_matcher.extract_entry(text)
            extracted_fields['entry'] = entry
            extracted_fields['stop_loss'] = self.pattern_matcher.extract_stop_loss(text)
            extracted_fields['take_profits'] = self.pattern_matcher.extract_take_profits(text)
        except Exception as e:
            logger.debug(f"Error extracting fields for error log: {e}")

        return ExtractionError(
            message_id=message_id,
            channel_username=channel_username,
            timestamp=timestamp,
            raw_message=text,
            error_reason=error_reason,
            extracted_fields=extracted_fields
        )
