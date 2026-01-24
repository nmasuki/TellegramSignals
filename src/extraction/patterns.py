"""Pattern matching for signal extraction using regex"""
import re
import logging
from typing import List, Optional, Tuple, Dict


logger = logging.getLogger(__name__)


# Unified pattern set that handles both Nick Alpha Trader and Gary Gold Legacy formats
UNIFIED_PATTERNS = {
    'symbol': [
        r'\b(GOLD|Gold)\b',
        r'\b(XAU/?USD)\b',
        r'\b([A-Z]{3}/?[A-Z]{3})\b',
    ],

    'direction': [
        r'\b(Buy|Sell)\s+Now\b',      # Gary Gold format
        r'\b(BUY|SELL)\s+now\b',      # Nick Alpha format
        r'\b(BUY|SELL)\b',            # Generic fallback
    ],

    'entry_range': [
        r'@\s*(\d+\.?\d*)-(\d+\.?\d*)',  # Handles both with/without space after @
    ],

    'entry_single': [
        r'@\s*(\d+\.?\d*)(?!-)',
    ],

    'stop_loss': [
        r'sl:\s*(\d+\.?\d*)',         # Handles both with/without space
        r'stop\s*loss:\s*(\d+\.?\d*)',
        r'stop:\s*(\d+\.?\d*)',
    ],

    'take_profit': [
        r'tp(\d+):\s*(\d+\.?\d*)',    # Handles both with/without space
        r'target\s*(\d+):\s*(\d+\.?\d*)',
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
        for pattern in UNIFIED_PATTERNS['stop_loss']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sl = float(match.group(1))
                logger.debug(f"Extracted stop loss: {sl}")
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

        for pattern in UNIFIED_PATTERNS['take_profit']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tp_num = int(match.group(1))
                tp_price = float(match.group(2))
                tps.append((tp_num, tp_price))
                logger.debug(f"Extracted TP{tp_num}: {tp_price}")

        # Sort by TP number
        tps.sort(key=lambda x: x[0])

        return tps

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
