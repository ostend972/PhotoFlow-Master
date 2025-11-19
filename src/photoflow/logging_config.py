"""
PhotoFlow Master - Logging Configuration
Centralized logging setup for consistent logging across the application.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .constants import (
    LOG_DIR_NAME,
    LOG_SUBDIR,
    LOG_FILE_FORMAT,
    LOG_DATE_FORMAT,
    LOG_MESSAGE_FORMAT,
)


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = False,
    log_dir: Optional[Path] = None,
) -> logging.Logger:
    """
    Setup logging configuration for PhotoFlow.

    Args:
        level: Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        log_dir: Custom log directory (uses default if None)

    Returns:
        Configured root logger

    Examples:
        >>> logger = setup_logging(level=logging.DEBUG, log_to_console=True)
        >>> logger.info("Application started")
    """
    # Determine log directory
    if log_dir is None:
        log_dir = Path.home() / "Documents" / LOG_DIR_NAME / LOG_SUBDIR

    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate log file name
    date_str = datetime.now().strftime(LOG_DATE_FORMAT)
    log_file = log_dir / LOG_FILE_FORMAT.format(date=date_str)

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_MESSAGE_FORMAT)

    # File handler
    if log_to_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Log startup
    root_logger.info("=" * 80)
    root_logger.info(f"PhotoFlow Master - Logging initialized")
    root_logger.info(f"Log level: {logging.getLevelName(level)}")
    if log_to_file:
        root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 80)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module loaded")
    """
    return logging.getLogger(name)
