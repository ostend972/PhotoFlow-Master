"""
PhotoFlow Master - EXIF Metadata Handler
Efficient extraction and caching of EXIF data from images.
"""

import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional, Generator

from PIL import Image
from PIL.ExifTags import TAGS

from .constants import (
    ALL_SUPPORTED_FORMATS,
    EXIF_DATE_TAG,
    EXIF_DATE_FORMAT,
    EXIF_CACHE_SIZE,
)
from .exceptions import EXIFError

logger = logging.getLogger(__name__)


class EXIFHandler:
    """
    Handler for extracting EXIF metadata from images.

    Uses LRU cache to avoid re-reading the same files.
    Supports all common RAW and processed image formats.
    """

    def __init__(self, cache_size: int = EXIF_CACHE_SIZE):
        """
        Initialize EXIF handler.

        Args:
            cache_size: Size of LRU cache for EXIF data
        """
        self.cache_size = cache_size
        self._extract_cached = lru_cache(maxsize=cache_size)(self._extract_date_uncached)

    def _extract_date_uncached(self, image_path: Path) -> Optional[datetime]:
        """
        Extract shooting date from image EXIF (uncached version).

        Args:
            image_path: Path to image file

        Returns:
            Datetime object if found, None otherwise

        Raises:
            EXIFError: If image cannot be opened or processed
        """
        try:
            with Image.open(image_path) as img:
                # Use getexif() instead of deprecated _getexif()
                exif_data = img.getexif()

                if not exif_data:
                    logger.debug(f"No EXIF data found in {image_path.name}")
                    return None

                # Look for DateTimeOriginal tag
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id)
                    if tag_name == EXIF_DATE_TAG:
                        try:
                            return datetime.strptime(str(value), EXIF_DATE_FORMAT)
                        except ValueError as e:
                            logger.warning(
                                f"Invalid date format in {image_path.name}: {value} - {e}"
                            )
                            return None

                logger.debug(f"No {EXIF_DATE_TAG} tag found in {image_path.name}")
                return None

        except (IOError, OSError) as e:
            raise EXIFError(image_path, f"Cannot open image: {e}")
        except Image.UnidentifiedImageError as e:
            raise EXIFError(image_path, f"Unidentified image format: {e}")
        except Exception as e:
            raise EXIFError(image_path, f"Unexpected error: {e}")

    def extract_date(self, image_path: Path) -> Optional[datetime]:
        """
        Extract shooting date from image EXIF (cached).

        Args:
            image_path: Path to image file

        Returns:
            Datetime object if found, None otherwise

        Raises:
            EXIFError: If image cannot be opened or processed
        """
        # Convert to absolute path for cache consistency
        abs_path = image_path.resolve()
        return self._extract_cached(abs_path)

    def find_earliest_date(
        self,
        source_path: Path,
        recursive: bool = True,
        callback: Optional[callable] = None,
    ) -> Optional[datetime]:
        """
        Find the earliest shooting date in a directory.

        Args:
            source_path: Directory to search
            recursive: Search recursively in subdirectories
            callback: Optional callback function called for each found date
                     Signature: callback(file_path, date)

        Returns:
            Earliest datetime found, or None if no dates found

        Examples:
            >>> handler = EXIFHandler()
            >>> handler.find_earliest_date(Path('/photos'))
            datetime.datetime(2023, 1, 15, 10, 30, 0)
        """
        earliest_date: Optional[datetime] = None
        files_checked = 0
        dates_found = 0

        for image_file in self._iter_supported_images(source_path, recursive):
            files_checked += 1

            try:
                date_taken = self.extract_date(image_file)

                if date_taken:
                    dates_found += 1

                    if earliest_date is None or date_taken < earliest_date:
                        earliest_date = date_taken
                        logger.info(
                            f"Earlier date found: {date_taken.strftime('%d-%m-%Y')} "
                            f"in {image_file.name}"
                        )

                        if callback:
                            callback(image_file, date_taken)

            except EXIFError as e:
                logger.warning(f"Skipping {image_file.name}: {e.reason}")
                continue

        logger.info(
            f"Scanned {files_checked} images, found {dates_found} with EXIF dates"
        )
        return earliest_date

    def _iter_supported_images(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Generator[Path, None, None]:
        """
        Iterate over supported image files in a directory.

        Args:
            directory: Directory to search
            recursive: Search recursively

        Yields:
            Path objects for supported image files
        """
        search_method = directory.rglob if recursive else directory.glob
        pattern = "*"

        for file_path in search_method(pattern):
            if not file_path.is_file():
                continue

            if file_path.suffix.upper() in ALL_SUPPORTED_FORMATS:
                yield file_path

    def clear_cache(self) -> None:
        """Clear the EXIF cache."""
        self._extract_cached.cache_clear()
        logger.debug("EXIF cache cleared")

    def cache_info(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hits, misses, size, and maxsize
        """
        info = self._extract_cached.cache_info()
        return {
            "hits": info.hits,
            "misses": info.misses,
            "size": info.currsize,
            "maxsize": info.maxsize,
            "hit_rate": info.hits / (info.hits + info.misses) if (info.hits + info.misses) > 0 else 0
        }
