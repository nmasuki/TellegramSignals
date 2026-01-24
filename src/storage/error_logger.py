"""Error logger for failed signal extractions"""
import json
import logging
from pathlib import Path
from typing import List
from datetime import datetime

from ..extraction.models import ExtractionError


logger = logging.getLogger(__name__)


class ErrorLogger:
    """Logs extraction errors to JSONL file"""

    def __init__(self, file_path: Path, encoding: str = 'utf-8'):
        """
        Initialize error logger

        Args:
            file_path: Path to error log file (JSONL format)
            encoding: File encoding
        """
        self.file_path = Path(file_path)
        self.encoding = encoding

        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Error logger initialized: {self.file_path}")

    def log_error(self, error: ExtractionError):
        """
        Log an extraction error

        Args:
            error: ExtractionError to log
        """
        try:
            # Convert to dict and then to JSON string
            error_dict = error.to_dict()
            json_line = json.dumps(error_dict, ensure_ascii=False)

            # Append to file
            with open(self.file_path, 'a', encoding=self.encoding) as f:
                f.write(json_line + '\n')

            logger.warning(
                f"Logged extraction error: {error.channel_username} - {error.error_reason}"
            )

        except Exception as e:
            logger.error(f"Failed to log extraction error: {e}", exc_info=True)

    def log_exception(self, exception: Exception, context: dict):
        """
        Log a general exception with context

        Args:
            exception: Exception that occurred
            context: Context dictionary (message_id, channel, etc.)
        """
        try:
            error_dict = {
                'error_type': 'exception',
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'context': context,
                'occurred_at': datetime.now().isoformat(),
            }

            json_line = json.dumps(error_dict, ensure_ascii=False)

            with open(self.file_path, 'a', encoding=self.encoding) as f:
                f.write(json_line + '\n')

            logger.error(f"Logged exception: {type(exception).__name__}: {exception}")

        except Exception as e:
            logger.error(f"Failed to log exception: {e}", exc_info=True)

    def read_errors(self, limit: int = None) -> List[dict]:
        """
        Read errors from log file

        Args:
            limit: Maximum number of errors to read (None = all)

        Returns:
            List of error dictionaries (most recent first if limit specified)
        """
        if not self.file_path.exists():
            return []

        errors = []

        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            error_dict = json.loads(line)
                            errors.append(error_dict)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse error log line: {e}")

            # Return most recent first if limit specified
            if limit:
                errors = errors[-limit:]

            return errors

        except Exception as e:
            logger.error(f"Failed to read error log: {e}")
            return []

    def get_error_count(self) -> int:
        """
        Get total number of errors logged

        Returns:
            Error count
        """
        if not self.file_path.exists():
            return 0

        count = 0
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                for _ in f:
                    count += 1
            return count
        except Exception as e:
            logger.error(f"Failed to count errors: {e}")
            return 0

    def get_recent_errors(self, limit: int = 10) -> List[dict]:
        """
        Get most recent errors

        Args:
            limit: Number of recent errors to return

        Returns:
            List of recent error dictionaries
        """
        return self.read_errors(limit=limit)

    def clear(self):
        """Clear all errors from log file"""
        try:
            self.file_path.unlink(missing_ok=True)
            logger.info("Cleared error log file")
        except Exception as e:
            logger.error(f"Failed to clear error log: {e}")
            raise IOError(f"Error log clear failed: {e}")
