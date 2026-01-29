"""Signal extractor - coordinates pattern matching and validation"""
import logging
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

        # Stop Loss
        stop_loss = self.pattern_matcher.extract_stop_loss(text)
        extracted_fields['stop_loss'] = stop_loss

        # Take Profits
        tp_list = self.pattern_matcher.extract_take_profits(text)
        take_profits = [tp_price for _, tp_price in tp_list]

        # If no absolute TPs found, try TP pips format
        if not take_profits:
            tp_pips = self.pattern_matcher.extract_take_profits_pips(text)
            if tp_pips:
                # Calculate TP prices from pips
                entry_ref = entry_single or (entry_min + entry_max) / 2 if entry_min and entry_max else None
                if entry_ref and direction:
                    take_profits = self._calculate_tp_from_pips(
                        entry_ref, direction, tp_pips, symbol
                    )
                    logger.debug(f"Calculated TPs from pips: {take_profits}")

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
        # Gold/XAUUSD: 1 pip = 0.1
        if symbol in ('XAUUSD', 'GOLD'):
            return 0.1
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

        # Entry (single or range)
        if extracted_fields.get('entry_price') or (
            extracted_fields.get('entry_price_min') and
            extracted_fields.get('entry_price_max')
        ):
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
