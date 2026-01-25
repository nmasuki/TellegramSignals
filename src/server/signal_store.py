"""In-memory signal store for MT5 EA integration"""
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

from ..extraction.models import Signal


@dataclass
class StoredSignal:
    """Signal with status tracking for MT5"""
    signal: Signal
    status: str = "pending"  # pending, acknowledged, expired
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None


class SignalStore:
    """
    Thread-safe in-memory signal store with persistence.

    Signals flow:
    1. New signal extracted -> add_signal() -> status: pending
    2. EA fetches signal -> get_pending_signals() -> returns pending signals
    3. EA acknowledges signal -> acknowledge_signal() -> status: acknowledged
    4. Old signals cleaned up -> cleanup_old_signals()
    """

    def __init__(self, persistence_path: Optional[str] = None, max_age_hours: int = 24):
        """
        Initialize signal store.

        Args:
            persistence_path: Path to JSON file for persistence (optional)
            max_age_hours: Maximum age of signals before cleanup
        """
        self._signals: Dict[str, StoredSignal] = {}
        self._lock = threading.RLock()
        self._persistence_path = Path(persistence_path) if persistence_path else None
        self._max_age = timedelta(hours=max_age_hours)

        # Load persisted signals on startup
        if self._persistence_path:
            self._load_from_file()

    def add_signal(self, signal: Signal) -> bool:
        """
        Add a new signal to the store.

        Args:
            signal: Extracted signal from Telegram

        Returns:
            True if added, False if duplicate
        """
        message_id = str(signal.message_id)

        with self._lock:
            # Check for duplicate
            if message_id in self._signals:
                return False

            self._signals[message_id] = StoredSignal(signal=signal)
            self._persist()
            return True

    def get_pending_signals(self, symbol: Optional[str] = None) -> List[dict]:
        """
        Get all pending signals, optionally filtered by symbol.

        Args:
            symbol: Filter by trading symbol (e.g., "XAUUSD")

        Returns:
            List of signal dictionaries for JSON response
        """
        with self._lock:
            results = []

            for stored in self._signals.values():
                if stored.status != "pending":
                    continue

                if symbol and stored.signal.symbol != symbol:
                    continue

                # Convert to dict format for MT5
                signal_dict = self._signal_to_mt5_dict(stored.signal)
                results.append(signal_dict)

            return results

    def acknowledge_signal(self, message_id: str) -> bool:
        """
        Mark signal as acknowledged by EA.

        Args:
            message_id: Telegram message ID

        Returns:
            True if acknowledged, False if not found
        """
        with self._lock:
            if message_id not in self._signals:
                return False

            self._signals[message_id].status = "acknowledged"
            self._signals[message_id].acknowledged_at = datetime.now()
            self._persist()
            return True

    def get_signal_status(self, message_id: str) -> Optional[str]:
        """Get status of a signal"""
        with self._lock:
            if message_id in self._signals:
                return self._signals[message_id].status
            return None

    def cleanup_old_signals(self) -> int:
        """
        Remove signals older than max_age.

        Returns:
            Number of signals removed
        """
        with self._lock:
            now = datetime.now()
            to_remove = []

            for msg_id, stored in self._signals.items():
                age = now - stored.created_at
                if age > self._max_age:
                    to_remove.append(msg_id)

            for msg_id in to_remove:
                del self._signals[msg_id]

            if to_remove:
                self._persist()

            return len(to_remove)

    def get_stats(self) -> dict:
        """Get store statistics"""
        with self._lock:
            pending = sum(1 for s in self._signals.values() if s.status == "pending")
            acknowledged = sum(1 for s in self._signals.values() if s.status == "acknowledged")

            return {
                "total": len(self._signals),
                "pending": pending,
                "acknowledged": acknowledged,
            }

    def _signal_to_mt5_dict(self, signal: Signal) -> dict:
        """Convert Signal to MT5-compatible dictionary"""
        return {
            "message_id": str(signal.message_id),
            "symbol": signal.symbol,
            "direction": signal.direction,
            "entry_price": signal.entry_price,
            "entry_price_min": signal.entry_price_min,
            "entry_price_max": signal.entry_price_max,
            "stop_loss": signal.stop_loss,
            "take_profits": signal.take_profits,
            "timestamp": signal.timestamp.isoformat() if signal.timestamp else None,
            "channel": signal.channel_username,
            "confidence": signal.confidence_score,
        }

    def _persist(self):
        """Save signals to file"""
        if not self._persistence_path:
            return

        try:
            data = {
                "version": 1,
                "updated_at": datetime.now().isoformat(),
                "signals": {}
            }

            for msg_id, stored in self._signals.items():
                data["signals"][msg_id] = {
                    "signal": stored.signal.to_dict(),
                    "status": stored.status,
                    "created_at": stored.created_at.isoformat(),
                    "acknowledged_at": stored.acknowledged_at.isoformat() if stored.acknowledged_at else None,
                }

            self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._persistence_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to persist signals: {e}")

    def _load_from_file(self):
        """Load signals from file"""
        if not self._persistence_path or not self._persistence_path.exists():
            return

        try:
            with open(self._persistence_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get("version") != 1:
                return

            for msg_id, stored_data in data.get("signals", {}).items():
                signal_dict = stored_data["signal"]

                # Reconstruct Signal object
                signal = Signal(
                    message_id=signal_dict["message_id"],
                    channel_username=signal_dict["channel_username"],
                    timestamp=datetime.fromisoformat(signal_dict["timestamp"]) if signal_dict.get("timestamp") else None,
                    symbol=signal_dict["symbol"],
                    direction=signal_dict["direction"],
                    entry_price=signal_dict.get("entry_price"),
                    entry_price_min=signal_dict.get("entry_price_min"),
                    entry_price_max=signal_dict.get("entry_price_max"),
                    stop_loss=signal_dict.get("stop_loss"),
                    take_profits=[
                        tp for tp in [
                            signal_dict.get("take_profit_1"),
                            signal_dict.get("take_profit_2"),
                            signal_dict.get("take_profit_3"),
                            signal_dict.get("take_profit_4"),
                        ] if tp is not None
                    ],
                    confidence_score=signal_dict.get("confidence_score", 0.0),
                    raw_message=signal_dict.get("raw_message", ""),
                    extraction_notes=signal_dict.get("extraction_notes", ""),
                )

                stored = StoredSignal(
                    signal=signal,
                    status=stored_data["status"],
                    created_at=datetime.fromisoformat(stored_data["created_at"]),
                    acknowledged_at=datetime.fromisoformat(stored_data["acknowledged_at"]) if stored_data.get("acknowledged_at") else None,
                )

                # Only load non-expired signals
                if datetime.now() - stored.created_at < self._max_age:
                    self._signals[msg_id] = stored

        except Exception as e:
            print(f"Warning: Failed to load persisted signals: {e}")
