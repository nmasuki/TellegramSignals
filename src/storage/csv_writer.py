"""CSV writer for signal output"""
import csv
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timedelta
import pandas as pd

from ..extraction.models import Signal


logger = logging.getLogger(__name__)


class CSVWriter:
    """Writes signals to CSV file"""

    # CSV field order (optimized for MT5 consumption - no raw message)
    FIELD_NAMES = [
        'message_id',
        'channel_username',
        'timestamp',
        'symbol',
        'direction',
        'entry_price',
        'entry_price_min',
        'entry_price_max',
        'stop_loss',
        'take_profit_1',
        'take_profit_2',
        'take_profit_3',
        'take_profit_4',
        'confidence_score',
        'extracted_at',
    ]

    def __init__(self, file_path: Path, encoding: str = 'utf-8'):
        """
        Initialize CSV writer

        Args:
            file_path: Path to CSV file
            encoding: File encoding
        """
        self.file_path = Path(file_path)
        self.encoding = encoding

        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file with header if it doesn't exist
        self._ensure_header()

        logger.info(f"CSV writer initialized: {self.file_path}")

    def _ensure_header(self):
        """Ensure CSV file exists with proper header"""
        if not self.file_path.exists():
            with open(self.file_path, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELD_NAMES)
                writer.writeheader()
            logger.info(f"Created new CSV file with header: {self.file_path}")

    def write_signal(self, signal: Signal):
        """
        Write a single signal to CSV

        Args:
            signal: Signal to write

        Raises:
            IOError: If write fails
        """
        try:
            # Convert signal to dict and filter to only include FIELD_NAMES
            signal_dict = signal.to_dict()
            filtered_dict = {k: v for k, v in signal_dict.items() if k in self.FIELD_NAMES}

            # Write to CSV
            with open(self.file_path, 'a', newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELD_NAMES, extrasaction='ignore')
                writer.writerow(filtered_dict)

            logger.info(
                f"Wrote signal to CSV: {signal.symbol} {signal.direction} "
                f"(message_id: {signal.message_id})"
            )

        except Exception as e:
            logger.error(f"Failed to write signal to CSV: {e}", exc_info=True)
            raise IOError(f"CSV write failed: {e}")

    def write_signals(self, signals: List[Signal]):
        """
        Write multiple signals to CSV

        Args:
            signals: List of signals to write

        Raises:
            IOError: If write fails
        """
        if not signals:
            logger.warning("No signals to write")
            return

        try:
            with open(self.file_path, 'a', newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELD_NAMES, extrasaction='ignore')
                for signal in signals:
                    signal_dict = signal.to_dict()
                    filtered_dict = {k: v for k, v in signal_dict.items() if k in self.FIELD_NAMES}
                    writer.writerow(filtered_dict)

            logger.info(f"Wrote {len(signals)} signals to CSV")

        except Exception as e:
            logger.error(f"Failed to write signals to CSV: {e}", exc_info=True)
            raise IOError(f"CSV batch write failed: {e}")

    def read_signals(self, limit: int = None) -> List[dict]:
        """
        Read signals from CSV

        Args:
            limit: Maximum number of signals to read (None = all)

        Returns:
            List of signal dictionaries
        """
        if not self.file_path.exists():
            return []

        try:
            df = pd.read_csv(self.file_path, encoding=self.encoding)

            if limit:
                df = df.tail(limit)

            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Failed to read signals from CSV: {e}")
            return []

    def get_signal_count(self) -> int:
        """
        Get total number of signals in CSV

        Returns:
            Signal count
        """
        if not self.file_path.exists():
            return 0

        try:
            df = pd.read_csv(self.file_path, encoding=self.encoding)
            return len(df)
        except Exception as e:
            logger.error(f"Failed to count signals: {e}")
            return 0

    def clear(self):
        """Clear all signals from CSV (keeps header)"""
        try:
            with open(self.file_path, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELD_NAMES)
                writer.writeheader()
            logger.info("Cleared all signals from CSV")
        except Exception as e:
            logger.error(f"Failed to clear CSV: {e}")
            raise IOError(f"CSV clear failed: {e}")

    def cleanup_old_records(self, max_age_hours: int = 12) -> int:
        """
        Remove records older than specified hours

        Args:
            max_age_hours: Maximum age of records to keep (default 12 hours)

        Returns:
            Number of records removed
        """
        if not self.file_path.exists():
            return 0

        try:
            df = pd.read_csv(self.file_path, encoding=self.encoding)

            if df.empty:
                return 0

            original_count = len(df)

            # Determine which datetime column to use
            date_column = None
            if 'extracted_at' in df.columns:
                date_column = 'extracted_at'
            elif 'timestamp' in df.columns:
                date_column = 'timestamp'
            else:
                # No date column - file is malformed, clear it
                logger.warning("No date column found, clearing CSV file")
                self.clear()
                return original_count

            # Parse date column as datetime
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            # Filter to keep only records within the time window
            df_filtered = df[df[date_column] >= cutoff_time]

            removed_count = original_count - len(df_filtered)

            if removed_count > 0:
                # Write filtered data back to CSV
                df_filtered.to_csv(self.file_path, index=False, encoding=self.encoding)
                logger.info(f"Cleaned up {removed_count} old records (older than {max_age_hours}h)")

            return removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}", exc_info=True)
            return 0
