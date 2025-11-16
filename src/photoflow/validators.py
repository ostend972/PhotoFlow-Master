"""
PhotoFlow Master - Validation Module
Input validation and sanitization utilities.
"""

import re
from pathlib import Path
from typing import Optional

import psutil

from .constants import (
    INVALID_FILENAME_CHARS,
    REPLACEMENT_CHAR,
    MAX_FILENAME_LENGTH,
    MAX_PATH_DEPTH,
    MIN_FREE_SPACE_GB,
)
from .exceptions import PathValidationError, InsufficientSpaceError


def sanitize_filename(name: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Sanitize filename to avoid OS conflicts and ensure safety.

    Args:
        name: The original filename to sanitize
        max_length: Maximum allowed filename length

    Returns:
        A sanitized filename safe for all operating systems

    Examples:
        >>> sanitize_filename('mon/fichier*.txt')
        'mon_fichier_.txt'
        >>> sanitize_filename('a' * 300)
        'aaa...aaa'  # Truncated to max_length
    """
    # Replace invalid characters
    sanitized = re.sub(INVALID_FILENAME_CHARS, REPLACEMENT_CHAR, name)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')

    # Ensure not empty
    if not sanitized:
        sanitized = 'unnamed'

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_path(
    path: Path,
    must_exist: bool = True,
    must_be_dir: bool = False,
    must_be_file: bool = False,
    check_readable: bool = True,
    check_writable: bool = False,
) -> None:
    """
    Validate a file system path with security checks.

    Args:
        path: Path to validate
        must_exist: Path must exist
        must_be_dir: Path must be a directory
        must_be_file: Path must be a file
        check_readable: Check if path is readable
        check_writable: Check if path is writable

    Raises:
        PathValidationError: If validation fails

    Examples:
        >>> validate_path(Path('/tmp'), must_exist=True, must_be_dir=True)
        >>> validate_path(Path('/nonexistent'))  # Raises PathValidationError
    """
    # Security: Check for path traversal attempts
    try:
        path = path.resolve(strict=False)
    except (OSError, RuntimeError) as e:
        raise PathValidationError(path, f"Cannot resolve path: {e}")

    # Check path depth (security against deep nesting attacks)
    if len(path.parts) > MAX_PATH_DEPTH:
        raise PathValidationError(path, f"Path depth exceeds {MAX_PATH_DEPTH}")

    # Existence check
    if must_exist and not path.exists():
        raise PathValidationError(path, "Path does not exist")

    # Type checks
    if must_be_dir and path.exists() and not path.is_dir():
        raise PathValidationError(path, "Path is not a directory")

    if must_be_file and path.exists() and not path.is_file():
        raise PathValidationError(path, "Path is not a file")

    # Permission checks
    if check_readable and path.exists():
        if not path.is_dir():
            # For files, try to check read permission
            try:
                path.read_bytes()[:1]  # Try to read 1 byte
            except PermissionError:
                raise PathValidationError(path, "Path is not readable")
        # For directories, check if we can list contents
        elif not path.is_dir():
            pass
        else:
            try:
                next(path.iterdir(), None)
            except PermissionError:
                raise PathValidationError(path, "Directory is not readable")

    if check_writable:
        # Check write permission on parent directory
        parent = path.parent if path.exists() else path
        if not parent.exists():
            raise PathValidationError(path, "Parent directory does not exist")

        # Try to create a test file
        test_file = parent / f".photoflow_write_test_{id(path)}"
        try:
            test_file.touch()
            test_file.unlink()
        except (PermissionError, OSError) as e:
            raise PathValidationError(path, f"Path is not writable: {e}")


def validate_date_format(date_str: str, format_str: str) -> bool:
    """
    Validate date string format.

    Args:
        date_str: Date string to validate
        format_str: Expected strptime format

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_date_format('31-12-2023', '%d-%m-%Y')
        True
        >>> validate_date_format('2023-12-31', '%d-%m-%Y')
        False
    """
    from datetime import datetime
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False


def check_disk_space(path: Path, required_gb: Optional[float] = None) -> float:
    """
    Check available disk space on the path's filesystem.

    Args:
        path: Path to check disk space for
        required_gb: Minimum required space in GB (uses MIN_FREE_SPACE_GB if None)

    Returns:
        Available space in GB

    Raises:
        InsufficientSpaceError: If available space is less than required

    Examples:
        >>> check_disk_space(Path('/tmp'))
        45.3  # Returns available GB
    """
    if required_gb is None:
        required_gb = MIN_FREE_SPACE_GB

    try:
        usage = psutil.disk_usage(str(path))
        available_gb = usage.free / (1024 ** 3)

        if available_gb < required_gb:
            raise InsufficientSpaceError(required_gb, available_gb, path)

        return available_gb
    except Exception as e:
        if isinstance(e, InsufficientSpaceError):
            raise
        raise PathValidationError(path, f"Cannot check disk space: {e}")


def estimate_directory_size(path: Path) -> int:
    """
    Estimate total size of a directory in bytes.

    Args:
        path: Directory path to measure

    Returns:
        Total size in bytes

    Examples:
        >>> estimate_directory_size(Path('/tmp/photos'))
        1073741824  # 1GB in bytes
    """
    total_size = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except (OSError, PermissionError):
                    continue  # Skip files we can't access
    except (OSError, PermissionError):
        pass

    return total_size
