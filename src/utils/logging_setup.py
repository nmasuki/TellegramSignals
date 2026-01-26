"""Logging configuration for Telegram Signal Extractor"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(config: dict, project_root: Optional[Path] = None) -> logging.Logger:
    """
    Configure logging for the application

    Args:
        config: Logging configuration dictionary
        project_root: Project root directory

    Returns:
        Configured root logger
    """
    if project_root is None:
        # Fallback for when project_root is not provided
        # Works in both development and PyInstaller bundle
        if getattr(sys, 'frozen', False):
            project_root = Path(sys.executable).parent
        else:
            project_root = Path(__file__).parent.parent.parent

    # Get logging configuration
    log_level = config.get('level', 'INFO')
    log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    date_format = config.get('date_format', '%Y-%m-%d %H:%M:%S')

    # Create formatter
    formatter = logging.Formatter(log_format, date_format)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    if config.get('console', {}).get('enabled', True):
        console_level = config.get('console', {}).get('level', 'INFO')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if config.get('file', {}).get('enabled', True):
        file_level = config.get('file', {}).get('level', 'DEBUG')
        file_path = config.get('file', {}).get('file_path', 'logs/system.log')

        # Make path absolute
        log_file = Path(file_path)
        if not log_file.is_absolute():
            log_file = project_root / log_file

        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler
        max_bytes = config.get('file', {}).get('max_bytes', 10485760)  # 10 MB
        backup_count = config.get('file', {}).get('backup_count', 10)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, file_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info(f"Logging configured - Level: {log_level}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
