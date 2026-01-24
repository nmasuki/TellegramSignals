"""Data models for signal extraction"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Signal:
    """Represents an extracted trading signal"""

    # Identifiers
    message_id: int
    channel_username: str
    timestamp: datetime

    # Trading data
    symbol: str  # e.g., "XAUUSD", "EURUSD"
    direction: str  # "BUY" or "SELL"

    # Entry prices
    entry_price: Optional[float] = None  # Single entry price
    entry_price_min: Optional[float] = None  # For range entries
    entry_price_max: Optional[float] = None  # For range entries

    # Risk management
    stop_loss: Optional[float] = None
    take_profits: List[float] = field(default_factory=list)  # [TP1, TP2, TP3, ...]

    # Metadata
    confidence_score: float = 0.0  # 0.0 to 1.0
    raw_message: str = ""
    extraction_notes: str = ""  # Any warnings or notes

    # Processing
    extracted_at: datetime = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> dict:
        """Convert signal to dictionary"""
        return {
            'message_id': self.message_id,
            'channel_username': self.channel_username,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'entry_price_min': self.entry_price_min,
            'entry_price_max': self.entry_price_max,
            'stop_loss': self.stop_loss,
            'take_profit_1': self.take_profits[0] if len(self.take_profits) > 0 else None,
            'take_profit_2': self.take_profits[1] if len(self.take_profits) > 1 else None,
            'take_profit_3': self.take_profits[2] if len(self.take_profits) > 2 else None,
            'take_profit_4': self.take_profits[3] if len(self.take_profits) > 3 else None,
            'confidence_score': self.confidence_score,
            'raw_message': self.raw_message,
            'extraction_notes': self.extraction_notes,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
        }

    def has_entry(self) -> bool:
        """Check if signal has entry price information"""
        return self.entry_price is not None or (
            self.entry_price_min is not None and self.entry_price_max is not None
        )

    def get_entry_average(self) -> Optional[float]:
        """Get average entry price"""
        if self.entry_price is not None:
            return self.entry_price
        elif self.entry_price_min is not None and self.entry_price_max is not None:
            return (self.entry_price_min + self.entry_price_max) / 2
        return None


@dataclass
class ExtractionError:
    """Represents a failed signal extraction"""

    message_id: int
    channel_username: str
    timestamp: datetime
    raw_message: str
    error_reason: str
    extracted_fields: dict = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> dict:
        """Convert error to dictionary"""
        return {
            'message_id': self.message_id,
            'channel_username': self.channel_username,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'raw_message': self.raw_message,
            'error_reason': self.error_reason,
            'extracted_fields': self.extracted_fields,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else None,
        }
