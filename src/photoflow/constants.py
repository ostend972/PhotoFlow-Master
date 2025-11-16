"""
PhotoFlow Master - Constants Module
All magic values and configuration constants in one place.
"""

from pathlib import Path
from typing import Final

# Supported image formats
SUPPORTED_RAW_FORMATS: Final[frozenset[str]] = frozenset([
    ".ARW",   # Sony
    ".CR2", ".CR3",  # Canon
    ".NEF",   # Nikon
    ".RAF",   # Fujifilm
    ".DNG",   # Adobe/Universal
    ".ORF",   # Olympus
    ".RW2",   # Panasonic
])

SUPPORTED_IMAGE_FORMATS: Final[frozenset[str]] = frozenset([
    ".JPG", ".JPEG",
    ".TIFF", ".TIF",
    ".PNG",
])

ALL_SUPPORTED_FORMATS: Final[frozenset[str]] = SUPPORTED_RAW_FORMATS | SUPPORTED_IMAGE_FORMATS

# EXIF tags
EXIF_DATE_TAG: Final[str] = "DateTimeOriginal"
EXIF_DATE_FORMAT: Final[str] = "%Y:%m:%d %H:%M:%S"

# Date formats
USER_DATE_FORMAT: Final[str] = "%d-%m-%Y"
ISO_DATE_FORMAT: Final[str] = "%Y-%m-%d"

# File system constraints
MAX_FILENAME_LENGTH: Final[int] = 255
INVALID_FILENAME_CHARS: Final[str] = r'[<>:"/\\|?*]'
REPLACEMENT_CHAR: Final[str] = '_'

# Project structure
PROJECT_ROOT_DIR: Final[str] = "PROJETS_PHOTO"
MAX_SOURCES: Final[int] = 10

PROJECT_STRUCTURE: Final[dict[str, list[str]]] = {
    "01_PRE-PRODUCTION": ["Moodboard", "References", "Brief"],
    "02_RAW": [],
    "03_SELECTS": [],
    "04_RETOUCHE": ["PSD", "FINALS"],
    "05_VIDEO": ["RUSH", "FINALS"],
    "06_ADMIN": ["Factures", "Contrats"],
}

# Logging configuration
LOG_DIR_NAME: Final[str] = "PhotoProManager"
LOG_SUBDIR: Final[str] = "logs"
LOG_FILE_FORMAT: Final[str] = "manager_{date}.log"
LOG_DATE_FORMAT: Final[str] = "%Y%m%d"
LOG_MESSAGE_FORMAT: Final[str] = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

# Performance settings
FILE_COPY_BUFFER_SIZE: Final[int] = 1024 * 1024  # 1MB
MAX_WORKERS: Final[int] = 4  # For concurrent file operations
EXIF_CACHE_SIZE: Final[int] = 128  # LRU cache size for EXIF data

# GUI settings
GUI_WINDOW_SIZE: Final[tuple[int, int]] = (900, 700)
GUI_TITLE: Final[str] = "📸 PhotoFlow Master - Gestionnaire de Projets Photo"
GUI_LOG_HEIGHT: Final[int] = 8
GUI_TREE_HEIGHT: Final[int] = 8

# Validation
MIN_FREE_SPACE_GB: Final[float] = 1.0  # Minimum free space required (GB)
MAX_PATH_DEPTH: Final[int] = 10  # Maximum allowed path depth for security
