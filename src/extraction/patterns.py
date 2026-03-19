"""Pattern matching for signal extraction using regex"""
import re
import logging
from typing import List, Optional, Tuple, Dict


logger = logging.getLogger(__name__)

# Subscript/superscript digit mapping → regular digits
_SCRIPT_MAP = str.maketrans('₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹', '01234567890123456789')


def _to_int(s: str) -> int:
    """Convert a string that may contain subscript/superscript digits to an int."""
    return int(s.translate(_SCRIPT_MAP))


# Unicode character classes for common Telegram message variants
DASH = r'[-–—−]'  # hyphen-minus, en-dash, em-dash, minus sign
COLON = r'[:：]'  # regular colon, fullwidth colon
AT_SIGN = r'[@＠]'  # regular @, fullwidth @
SPACE = r'[\s\u00A0]'  # whitespace including non-breaking space
# regular digits + subscript ₀-₉ + superscript ⁰¹²³⁴⁵⁶⁷⁸⁹
DIGIT = r'[\d\u2080-\u2089\u2070\u00B9\u00B2\u00B3\u2074-\u2079]'


# Unified pattern set that handles both Nick Alpha Trader and Gary Gold Legacy formats
# Uses Unicode-aware character classes to handle Telegram message variants
UNIFIED_PATTERNS = {
    'symbol': [
        r'\b(GOLD|Gold)\b',
        r'\b(XAU/?USD)\b',
        r'\b(SILVER|Silver|Slver|SLVER)\b',  # Silver including common typo
        r'\b(XAG/?USD)\b',
        r'\b(US30|DJ30|DOW|Dow\s*Jones)\b',  # US30 / Dow Jones index
        # Match only valid currency code pairs (not random words like PUBLIC, EASYYY)
        r'\b((?:EUR|GBP|AUD|NZD|USD|CAD|CHF|JPY|BTC|ETH)/?(?:EUR|GBP|AUD|NZD|USD|CAD|CHF|JPY|BTC|ETH))\b',
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
        rf'\b(?:BUY|SELL){SPACE}*{AT_SIGN}{SPACE}*(\d+\.?\d*)(?!{DASH})',  # BUY/SELL @price format (e.g., "BUY @ 2650")
        rf'\b(?:BUY|SELL){SPACE}+(?:GOLD|XAUUSD|SILVER|XAGUSD){SPACE}*{AT_SIGN}{SPACE}*(\d+\.?\d*)(?!{DASH})',  # Buy Gold @4776 format
        rf'\b(?:BUY|SELL){SPACE}+(\d+\.?\d*)(?!{DASH})',  # BUY/SELL price format (e.g., "SELL 78300")
    ],

    'stop_loss': [
        rf'sl{SPACE}*{COLON}{SPACE}*(\d+\.?\d*)',   # sl: 1234, sl : 1234 formats
        rf'\bSL{SPACE}*{AT_SIGN}{SPACE}*(\d+\.?\d*)',  # SL @ 80200, SL@ 80200 formats
        rf'\bSL{SPACE}+(\d+\.?\d*)(?!{SPACE}*pips)',  # SL 1234 format (no colon, not followed by pips)
        rf'si{SPACE}*{COLON}{SPACE}*(\d+\.?\d*)',   # si: 1234, si : 1234 formats (common typo)
        rf'\bSI{SPACE}+(\d+\.?\d*)(?!{SPACE}*pips)',  # SI 1234 format (common typo, not followed by pips)
        rf'stop\W*loss{SPACE}*{COLON}?{SPACE}*(\d+\.?\d*)(?!{SPACE}*pips)',  # Stop Loss formats (not followed by pips)
        rf'stop{SPACE}*{COLON}{SPACE}*(\d+\.?\d*)',
        rf'\bStop{SPACE}+(\d+\.?\d*)(?!{SPACE}*pips)',  # Stop 1234 format (not followed by pips)
    ],

    'take_profit': [
        rf'tp{SPACE}*({DIGIT}){COLON}{SPACE}*(\d+\.?\d*)',         # tp1: 5085, tp₁: 5085 format
        rf'tp{SPACE}*({DIGIT}){SPACE}+(\d{{3,}}\.?\d*)',           # tp 1 5085, tp₁ 5085 format
        rf'target{SPACE}*({DIGIT}){COLON}?{SPACE}*(\d{{3,}}\.?\d*)',  # target1: 5085 formats
        rf'\bT{SPACE}*({DIGIT}){COLON}{SPACE}*(\d+\.?\d*)',        # T1: 5085, T₁: 5085 format
        rf'\bT{SPACE}*({DIGIT}){SPACE}+(\d{{3,}}\.?\d*)',          # T 1 5085, T₁ 5085 format
        rf'take\W*profit{SPACE}*({DIGIT}){COLON}?{SPACE}*(\d{{3,}}\.?\d*)',  # Take Profit 1: 5085
    ],

    'take_profit_single': [
        rf'\btp{COLON}{SPACE}*(\d+\.?\d*)',         # tp: 1234 format (no number)
        rf'\btarget{COLON}{SPACE}*(\d+\.?\d*)',     # target: 1234 format
        rf'\bT{COLON}{SPACE}*(\d+\.?\d*)',          # T: 1234 format
        rf'take\W*profit{SPACE}*{COLON}?{SPACE}*(\d+\.?\d*)',  # Take Profit: 1234, TakeProfit 1234 formats
        rf'\bTP\.?{SPACE}+(\d{{3,}}\.?\d*)',        # TP. 4835, TP 4835 (no number, dot optional)
    ],

    'stop_loss_numbered': [
        rf'stop{SPACE}*({DIGIT}+){COLON}?{SPACE}*(\d+\.?\d*)',    # stop1:, stop₁ 5073 formats
        rf'\bSL{SPACE}*({DIGIT}+){COLON}?{SPACE}*(\d+\.?\d*)',    # SL1:, SL₁ 5073 formats
    ],

    'take_profit_pips': [
        rf'\bTP{SPACE}+(\d+){SPACE}*{DASH}{SPACE}*(\d+){SPACE}*pips',  # TP 30-100pips format
        rf'\bTP{SPACE}+(\d+){SPACE}*pips',                              # TP 30pips format
    ],

    'take_profit_pips_numbered': [
        rf'\btp{SPACE}*({DIGIT}){SPACE}+(\d+){SPACE}*pips',  # tp1 3pips, tp₁ 3pips format
    ],

    'stop_loss_pips': [
        rf'\bSL{SPACE}+(\d+){SPACE}*pips',                              # SL 20pips format
        rf'\bsl{SPACE}+(\d+){SPACE}*pips',                              # sl 20pips format
        rf'stop\W*loss{SPACE}+(\d+){SPACE}*pips',                       # Stop Loss 20pips format
    ],

    'close_signal': [
        r'\bclose\s+all\b',                                             # "close all"
        r'\bclose\s+all\s+(?:trades?|positions?|orders?)\b',            # "close all trades/positions"
        r'\bclose\s+(?:trades?|positions?|orders?)\b',                  # "close trades/positions"
        r'\bexit\s+all\b',                                              # "exit all"
        r'\bexit\s+(?:trades?|positions?)\b',                           # "exit trades/positions"
        r'\bclose\s+(?:it|now|here)\b',                                 # "close it", "close now"
        r'\bclose\s+(?:buy|sell)\b',                                    # "close buy", "close sell"
        r'\bbook\s+profit\b',                                           # "book profit"
        r'\btake\s+profit\s+now\b',                                     # "take profit now"
        r'\bready\s+for\s+next\b',                                      # "ready for next" (implies close)
    ],

    'break_even': [
        r'\bmove\s+(?:sl|stop\s*loss?)\s+(?:to\s+)?(?:be|break\s*even|entry)\b',  # "move SL to BE"
        r'\bset\s+(?:sl|stop\s*loss?)\s+(?:to\s+)?(?:be|break\s*even|entry)\b',   # "set SL to BE"
        r'\b(?:sl|stop\s*loss?)\s+(?:to\s+)?(?:be|break\s*even|entry)\b',          # "SL to BE"
        r'\bbreak\s*even\b',                                                        # "break even" / "breakeven"
        r'\bsecure\s+(?:entry|position|trade)\b',                                   # "secure entry"
    ],

    'tp_hit': [
        r'\btp\s*\d?\s+(?:hit|done|reached|touched|secured)\b',         # "TP1 hit", "TP done"
        r'\b(?:hit|done|reached|touched|secured)\s+tp\s*\d?\b',         # "hit TP1", "done TP"
        r'\btp\s+hit\s+\d+\s*pips?\b',                                  # "TP Hit 150 pips"
        r'\brunning\s+\d+\s*pips?\b',                                   # "running 100 pips"
        r'\b\d+\s*pips?\s*(?:profit|done|secured|running)\b',           # "100 pips profit"
    ],

    'partial_close': [
        r'\bsecured?\s+(?:your\s+)?profit\s+higher\b',                  # "secured your profit higher entry"
        r'\bclose\s+higher\s+(?:entry|entries|positions?)\b',            # "close higher entries"
        r'\bhold\s+(?:lowest|lower|last)\s+(?:entry|entries|positions?)\b',  # "hold lowest entry"
        r'\bcollect\s+(?:fast\s+)?(?:money|profit)\b',                   # "collect fast money"
        r'\bpartial\s+close\b',                                          # "partial close"
        r'\bclose\s+(?:partial|some|half)\b',                            # "close partial/some/half"
        r'\bsecure\s+(?:your\s+)?profit\b',                             # "secure your profit"
    ],
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
            'SILVER': 'XAGUSD',
            'Silver': 'XAGUSD',
            'Slver': 'XAGUSD',   # Common typo (missing 'i')
            'SLVER': 'XAGUSD',   # Common typo (missing 'i')
            'XAG/USD': 'XAGUSD',
            'XAGUSD': 'XAGUSD',
            'EUR/USD': 'EURUSD',
            'EURUSD': 'EURUSD',
            'GBP/USD': 'GBPUSD',
            'GBPUSD': 'GBPUSD',
            'USD/JPY': 'USDJPY',
            'USDJPY': 'USDJPY',
            'GBP/JPY': 'GBPJPY',
            'GBPJPY': 'GBPJPY',
            'US30': 'US30',
            'DJ30': 'US30',
            'DOW': 'US30',
            'Dow Jones': 'US30',
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
                tp_num = _to_int(match.group(1))
                tp_price = float(match.group(2))
                tps.append((tp_num, tp_price))
                logger.debug(f"Extracted TP{tp_num}: {tp_price}")

        # If no numbered TPs found, try single TP patterns (tp:, target:, TP. price)
        # Each pattern is tried; break on first pattern that yields matches
        if not tps:
            for pattern in UNIFIED_PATTERNS['take_profit_single']:
                found = list(re.finditer(pattern, text, re.IGNORECASE))
                if found:
                    for i, match in enumerate(found, start=1):
                        tp_price = float(match.group(1))
                        tps.append((i, tp_price))
                        logger.debug(f"Extracted TP{i}: {tp_price} (from single pattern)")
                    break  # Use first matching pattern only

        # Sort by TP number
        tps.sort(key=lambda x: x[0])

        return tps

    def extract_take_profits_pips(self, text: str) -> Optional[Tuple[int, Optional[int]]]:
        """
        Extract take profit in pips format from text (range or single value)

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

    def extract_take_profits_pips_numbered(self, text: str) -> List[Tuple[int, int]]:
        """
        Extract numbered take profits in pips format (tp1 3pips, tp2 4pips, etc.)

        Args:
            text: Message text

        Returns:
            List of tuples (tp_number, pips), sorted by tp_number
        """
        tps = []

        for pattern in UNIFIED_PATTERNS['take_profit_pips_numbered']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tp_num = _to_int(match.group(1))
                tp_pips = int(match.group(2))
                tps.append((tp_num, tp_pips))
                logger.debug(f"Extracted TP{tp_num}: {tp_pips} pips")

        # Sort by TP number
        tps.sort(key=lambda x: x[0])

        return tps

    def extract_stop_loss_pips(self, text: str) -> Optional[int]:
        """
        Extract stop loss in pips format from text

        Args:
            text: Message text

        Returns:
            Stop loss in pips or None
        """
        for pattern in UNIFIED_PATTERNS['stop_loss_pips']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pips = int(match.group(1))
                logger.debug(f"Extracted SL pips: {pips}")
                return pips
        return None

    def is_close_signal(self, text: str) -> bool:
        """Check if message is a close/exit signal."""
        text_lower = text.lower()
        # Must contain a close-related keyword
        close_keywords = ['close', 'exit', 'book profit', 'ready for next']
        if not any(kw in text_lower for kw in close_keywords):
            return False
        for pattern in UNIFIED_PATTERNS.get('close_signal', []):
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def is_break_even_signal(self, text: str) -> bool:
        """Check if message is a break-even signal."""
        for pattern in UNIFIED_PATTERNS.get('break_even', []):
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def is_tp_hit_signal(self, text: str) -> bool:
        """Check if message indicates a take profit was hit."""
        for pattern in UNIFIED_PATTERNS.get('tp_hit', []):
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def is_partial_close_signal(self, text: str) -> bool:
        """Check if message is a partial close signal (close some, hold rest)."""
        for pattern in UNIFIED_PATTERNS.get('partial_close', []):
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def extract_close_direction(self, text: str) -> Optional[str]:
        """Extract if close is for a specific direction (BUY/SELL) or all."""
        if re.search(r'\bclose\s+buy\b', text, re.IGNORECASE):
            return 'BUY'
        if re.search(r'\bclose\s+sell\b', text, re.IGNORECASE):
            return 'SELL'
        return None  # Close all directions

    def extract_close_symbol(self, text: str) -> Optional[str]:
        """Extract if close is for a specific symbol."""
        return self.extract_symbol(text)

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
