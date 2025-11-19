"""
PhotoFlow Master - Custom Exceptions
Specific exception classes for better error handling.
"""

from pathlib import Path
from typing import Optional


class PhotoFlowError(Exception):
    """Base exception for all PhotoFlow errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize PhotoFlow error.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ValidationError(PhotoFlowError):
    """Raised when input validation fails."""
    pass


class PathValidationError(ValidationError):
    """Raised when a file path is invalid or unsafe."""

    def __init__(self, path: Path, reason: str):
        super().__init__(
            f"Invalid path: {path}",
            {"path": str(path), "reason": reason}
        )
        self.path = path
        self.reason = reason


class InsufficientSpaceError(PhotoFlowError):
    """Raised when there's not enough disk space."""

    def __init__(self, required_gb: float, available_gb: float, path: Path):
        super().__init__(
            f"Insufficient disk space on {path}",
            {
                "required_gb": required_gb,
                "available_gb": available_gb,
                "path": str(path)
            }
        )
        self.required_gb = required_gb
        self.available_gb = available_gb
        self.path = path


class EXIFError(PhotoFlowError):
    """Raised when EXIF data extraction fails."""

    def __init__(self, image_path: Path, reason: str):
        super().__init__(
            f"Failed to extract EXIF from {image_path.name}",
            {"image_path": str(image_path), "reason": reason}
        )
        self.image_path = image_path
        self.reason = reason


class FileOperationError(PhotoFlowError):
    """Raised when file operations fail."""

    def __init__(self, operation: str, source: Path, destination: Optional[Path] = None, reason: str = ""):
        details = {"operation": operation, "source": str(source)}
        if destination:
            details["destination"] = str(destination)
        if reason:
            details["reason"] = reason

        super().__init__(
            f"File operation '{operation}' failed for {source.name}",
            details
        )
        self.operation = operation
        self.source = source
        self.destination = destination


class ProjectStructureError(PhotoFlowError):
    """Raised when project structure creation fails."""
    pass


class NoSourcesError(PhotoFlowError):
    """Raised when no valid sources are provided."""

    def __init__(self):
        super().__init__("No valid sources provided")


class DateExtractionError(PhotoFlowError):
    """Raised when date extraction fails for all images in a source."""

    def __init__(self, source_path: Path):
        super().__init__(
            f"Could not extract date from any image in {source_path.name}",
            {"source_path": str(source_path)}
        )
        self.source_path = source_path
