"""
PhotoFlow Master - Professional Photo Project Manager
A Python application for organizing professional photography projects.
"""

__version__ = "2.0.0"
__author__ = "PhotoFlow Team"
__license__ = "MIT"

from .core import PhotoFlowManager, SourceInfo, ProjectResult
from .exif_handler import EXIFHandler
from .file_manager import FileManager, CopyResult
from .logging_config import setup_logging, get_logger
from .validators import (
    sanitize_filename,
    validate_path,
    validate_date_format,
    check_disk_space,
    estimate_directory_size,
)
from .exceptions import (
    PhotoFlowError,
    ValidationError,
    PathValidationError,
    InsufficientSpaceError,
    EXIFError,
    FileOperationError,
    ProjectStructureError,
    NoSourcesError,
    DateExtractionError,
)

__all__ = [
    "__version__",
    # Core classes
    "PhotoFlowManager",
    "SourceInfo",
    "ProjectResult",
    # Handlers
    "EXIFHandler",
    "FileManager",
    "CopyResult",
    # Utilities
    "setup_logging",
    "get_logger",
    "sanitize_filename",
    "validate_path",
    "validate_date_format",
    "check_disk_space",
    "estimate_directory_size",
    # Exceptions
    "PhotoFlowError",
    "ValidationError",
    "PathValidationError",
    "InsufficientSpaceError",
    "EXIFError",
    "FileOperationError",
    "ProjectStructureError",
    "NoSourcesError",
    "DateExtractionError",
]
