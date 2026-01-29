"""Pattern matching for signal extraction using regex"""
import re
import logging
from typing import List, Optional, Tuple, Dict


logger = logging.getLogger(__name__)


# Unicode character classes for common Telegram message variants
DASH = r'[-–—−]'  # hyphen-minus, en-dash, em-dash, minus sign
COLON = r'[:：]'  # regular colon, fullwidth colon
AT_SIGN = r'[@＠]'  # regular @, fullwidth @
SPACE = r'[\s\u00A0]'  # whitespace including non-breaking space


# Unified pattern set that handles both Nick Alpha Trader and Gary Gold Legacy formats
# Uses Unicode-aware character classes to handle Telegram message variants
UNIFIED_PATTERNS = {
    'symbol': [
        r'\b(GOLD|Gold)\b',
        r'\b(XAU/?USD)\b',
        r'\b([A-Z]{3}/?[A-Z]{3})\b',
    ],

    'direction': [
        rf'\b(Buy|Sell){SPACE}+Now\b',      # Gary Gold format
        rf'\b(BUY|SELL){SPACE}+now\b',      # Nick Alpha format
        rf'\b(Buy|Sell){SPACE}+again\b',    # Re-entry signal
        rf'\b(BUY|SELL){SPACE}+again\b',    # Re-entry signal (uppercase)
        rf'\b(Buy|Sell){SPACE}+Gold\b',     # "Buy Gold" format
        rf'\b(BUY|SELL){SPACE}+GOLD\b',     # "BUY GOLD" format
        r'\b(BUY|SELL)\b',                   # Generic fallback
    ],

    'entry_range': [
        rf'{AT_SIGN}{SPACE}*(\d+\.?\d*){DASH}(\d+\.?\d*)',  # @price1-price2 format
        rf'\b(?:buy|sell){SPACE}+(?:now{SPACE}+)?(?:again{SPACE}+)?(\d+){SPACE}*{DASH}{SPACE}*(\d+)',  # "buy 5070-5066" format
    ],

    'entry_single': [
        rf'{AT_SIGN}{SPACE}*(\d+\.?\d*)(?!{DASH})',  # @price format (not followed by dash)
        rf'\b(?:BUY|SELL){SPACE}+(\d+\.?\d*)(?!{DASH})',  # BUY/SELL price format (e.g., "SELL 3120.00")
    ],

    'stop_loss': [
        rf'sl{SPACE}*{COLON}{SPACE}*(\d+\.?\d*)',   # sl: 1234, sl : 1234 formats
        rf'\bSL{SPACE}+(\d+\.?\d*)',                 # SL 1234 format (no colon)
        rf'si{SPACE}*{COLON}{SPACE}*(\d+\.?\d*)',   # si: 1234, si : 1234 formats (common typo)
        rf'\bSI{SPACE}+(\d+\.?\d*)',                 # SI 1234 format (common typo)
        rf'stop\W*loss{SPACE}*{COLON}?{SPACE}*(\d+\.?\d*)',  # Stop Loss, StopLoss, Stop-Loss formats
        rf'stop{SPACE}*{COLON}{SPACE}*(\d+\.?\d*)',
        rf'\bStop{SPACE}+(\d+\.?\d*)',              # Stop 1234 format
    ],

    'take_profit': [
        rf'tp{SPACE}*(\d+){COLON}?{SPACE}*(\d+\.?\d*)',      # tp1:, tp 1, tp1 5085 formats
        rf'target{SPACE}*(\d+){COLON}?{SPACE}*(\d+\.?\d*)',  # target1:, target 1 5085 formats
        rf'\bT{SPACE}*(\d+){COLON}?{SPACE}*(\d+\.?\d*)',     # T1:, T 1, T1 5085 formats
        rf'take\W*profit{SPACE}*(\d+){COLON}?{SPACE}*(\d+\.?\d*)',  # Take Profit 1, TakeProfit1 formats
    ],

    'take_profit_single': [
        rf'\btp{COLON}{SPACE}*(\d+\.?\d*)',         # tp: 1234 format (no number)
        rf'\btarget{COLON}{SPACE}*(\d+\.?\d*)',     # target: 1234 format
        rf'\bT{COLON}{SPACE}*(\d+\.?\d*)',          # T: 1234 format
        rf'take\W*profit{SPACE}*{COLON}?{SPACE}*(\d+\.?\d*)',  # Take Profit: 1234, TakeProfit 1234 formats
    ],

    'stop_loss_numbered': [
        rf'stop{SPACE}*(\d+){COLON}?{SPACE}*(\d+\.?\d*)',    # stop1:, stop 1, stop1 5073 formats
        rf'\bSL{SPACE}*(\d+){COLON}?{SPACE}*(\d+\.?\d*)',    # SL1:, SL 1, SL1 5073 formats
    ],

    'take_profit_pips': [
        rf'\bTP{SPACE}+(\d+){SPACE}*{DASH}{SPACE}*(\d+){SPACE}*pips',  # TP 30-100pips format
        rf'\bTP{SPACE}+(\d+){SPACE}*pips',                              # TP 30pips format
    ]
}


class PatternMatcher:
    """Pattern matching for signal extraction"""

    def __init__(self, symbol_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize pattern matcher

        Args:
            symbol_mapping: Dictionary mapping symbol variations to normalized symbols
        """
        self.symbol_mapping = symbol_mapping or {
            'GOLD': 'XAUUSD',
            'Gold': 'XAUUSD',
            'XAU/USD': 'XAUUSD',
            'XAUUSD': 'XAUUSD',
            'EUR/USD': 'EURUSD',
            'EURUSD': 'EURUSD',
            'GBP/USD': 'GBPUSD',
            'GBPUSD': 'GBPUSD',
            'BTC/USD': 'BTCUSD',
            'BTCUSD': 'BTCUSD',
        }

    def extract_symbol(self, text: str) -> Optional[str]:
        """
        Extract trading symbol from text

        Args:
            text: Message text

        Returns:
            Normalized symbol or None
        """
        for pattern in UNIFIED_PATTERNS['symbol']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol = match.group(1)
                # Normalize symbol
                normalized = self._normalize_symbol(symbol)
                logger.debug(f"Extracted symbol: {symbol} -> {normalized}")
                return normalized
        return None

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol using mapping"""
        # Try exact match first
        if symbol in self.symbol_mapping:
            return self.symbol_mapping[symbol]

        # Try case-insensitive match
        symbol_upper = symbol.upper()
        for key, value in self.symbol_mapping.items():
            if key.upper() == symbol_upper:
                return value

        # Return as-is if no mapping found
        return symbol.upper()

    def extract_direction(self, text: str) -> Optional[str]:
        """
        Extract trade direction (BUY/SELL) from text

        Args:
            text: Message text

        Returns:
            "BUY" or "SELL" or None
        """
        for pattern in UNIFIED_PATTERNS['direction']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                direction = match.group(1).upper()
                logger.debug(f"Extracted direction: {direction}")
                return direction
        return None

    def extract_entry(self, text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Extract entry price(s) from text

        Args:
            text: Message text

        Returns:
            Tuple of (single_entry, entry_min, entry_max)
            - For single entry: (price, None, None)
            - For range entry: (None, min, max)
        """
        # Try range format first
        for pattern in UNIFIED_PATTERNS['entry_range']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price1 = float(match.group(1))
                price2 = float(match.group(2))

                # Normalize to min/max (order may vary in Gary Gold Legacy)
                entry_min = min(price1, price2)
                entry_max = max(price1, price2)

                logger.debug(f"Extracted entry range: {entry_min} - {entry_max}")
                return (None, entry_min, entry_max)

        # Try single entry
        for pattern in UNIFIED_PATTERNS['entry_single']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entry_price = float(match.group(1))
                logger.debug(f"Extracted single entry: {entry_price}")
                return (entry_price, None, None)

        return (None, None, None)

    def extract_stop_loss(self, text: str) -> Optional[float]:
        """
        Extract stop loss level from text

        Args:
            text: Message text

        Returns:
            Stop loss price or None
        """
        # Try standard SL patterns first
        for pattern in UNIFIED_PATTERNS['stop_loss']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sl = float(match.group(1))
                logger.debug(f"Extracted stop loss: {sl}")
                return sl

        # Try numbered SL patterns (stop1:, SL1:, etc.)
        for pattern in UNIFIED_PATTERNS['stop_loss_numbered']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sl = float(match.group(2))  # group(1) is the number, group(2) is the price
                logger.debug(f"Extracted stop loss: {sl} (from numbered pattern)")
                return sl

        return None

    def extract_take_profits(self, text: str) -> List[Tuple[int, float]]:
        """
        Extract take profit levels from text

        Args:
            text: Message text

        Returns:
            List of tuples (tp_number, price), sorted by tp_number
        """
        tps = []

        # Try numbered TP patterns first (tp1:, tp2:, T1:, target1:)
        for pattern in UNIFIED_PATTERNS['take_profit']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tp_num = int(match.group(1))
                tp_price = float(match.group(2))
                tps.append((tp_num, tp_price))
                logger.debug(f"Extracted TP{tp_num}: {tp_price}")

        # If no numbered TPs found, try single TP patterns (tp:, target:, T:)
        if not tps:
            for pattern in UNIFIED_PATTERNS['take_profit_single']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for i, match in enumerate(matches, start=1):
                    tp_price = float(match.group(1))
                    tps.append((i, tp_price))
                    logger.debug(f"Extracted TP{i}: {tp_price} (from single pattern)")

        # Sort by TP number
        tps.sort(key=lambda x: x[0])

        return tps

    def extract_take_profits_pips(self, text: str) -> Optional[Tuple[int, Optional[int]]]:
        """
        Extract take profit in pips format from text

        Args:
            text: Message text

        Returns:
            Tuple of (min_pips, max_pips) or (pips, None) for single value, or None
        """
        # Try range format first: "TP 30-100pips"
        for pattern in UNIFIED_PATTERNS['take_profit_pips']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex == 2:
                    # Range format
                    pips1 = int(match.group(1))
                    pips2 = int(match.group(2))
                    logger.debug(f"Extracted TP pips range: {pips1}-{pips2}")
                    return (min(pips1, pips2), max(pips1, pips2))
                else:
                    # Single value format
                    pips = int(match.group(1))
                    logger.debug(f"Extracted TP pips: {pips}")
                    return (pips, None)
        return None

    def is_signal(self, text: str) -> bool:
        """
        Quick check if message might be a signal

        Args:
            text: Message text

        Returns:
            True if message contains signal keywords
        """
        signal_keywords = ['buy', 'sell', 'entry', 'tp', 'sl', 'stop', 'target']
        text_lower = text.lower()

        return any(keyword in text_lower for keyword in signal_keywords)
