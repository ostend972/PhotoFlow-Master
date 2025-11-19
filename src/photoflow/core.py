"""
PhotoFlow Master - Core Manager Module
Main business logic for photo project management.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .constants import (
    PROJECT_ROOT_DIR,
    ISO_DATE_FORMAT,
    USER_DATE_FORMAT,
)
from .exif_handler import EXIFHandler
from .file_manager import FileManager, CopyResult
from .validators import validate_path, check_disk_space, estimate_directory_size

logger = logging.getLogger(__name__)


@dataclass
class SourceInfo:
    """Information about a source directory."""
    path: Path
    name: str
    date: Optional[str] = None  # ISO format: YYYY-MM-DD

    def __post_init__(self):
        """Validate after initialization."""
        validate_path(self.path, must_exist=True, must_be_dir=True)


@dataclass
class ProjectResult:
    """Result of project creation."""
    source: SourceInfo
    project_path: Path
    copy_results: list[CopyResult]
    success: bool
    error: Optional[str] = None

    @property
    def files_copied(self) -> int:
        """Number of successfully copied files."""
        return sum(1 for r in self.copy_results if r.success)

    @property
    def files_failed(self) -> int:
        """Number of failed file copies."""
        return sum(1 for r in self.copy_results if not r.success)

    @property
    def files_renamed(self) -> int:
        """Number of files renamed due to collision."""
        return sum(1 for r in self.copy_results if r.renamed)


class PhotoFlowManager:
    """
    Main manager for PhotoFlow operations.

    Coordinates EXIF extraction, file organization, and project structure creation.
    """

    def __init__(
        self,
        exif_handler: Optional[EXIFHandler] = None,
        file_manager: Optional[FileManager] = None,
    ):
        """
        Initialize PhotoFlow manager.

        Args:
            exif_handler: Optional custom EXIF handler
            file_manager: Optional custom file manager
        """
        self.exif_handler = exif_handler or EXIFHandler()
        self.file_manager = file_manager or FileManager()

    def detect_date(
        self,
        source: SourceInfo,
        callback: Optional[callable] = None
    ) -> Optional[str]:
        """
        Detect shooting date from source directory.

        Args:
            source: Source information
            callback: Optional callback for progress (file_path, date)

        Returns:
            Date string in ISO format (YYYY-MM-DD) or None
        """
        logger.info(f"Detecting date for {source.name} from {source.path}")

        earliest_date = self.exif_handler.find_earliest_date(
            source.path,
            recursive=True,
            callback=callback
        )

        if earliest_date:
            date_str = earliest_date.strftime(ISO_DATE_FORMAT)
            logger.info(f"Date detected: {date_str}")
            return date_str

        logger.warning(f"No date found in EXIF data for {source.name}")
        return None

    def create_project(
        self,
        source: SourceInfo,
        base_drive: Path,
        progress_callback: Optional[callable] = None,
    ) -> ProjectResult:
        """
        Create a complete project from a source.

        Args:
            source: Source information with path, name, and date
            base_drive: Base drive where to create project
            progress_callback: Optional callback for file copy progress

        Returns:
            ProjectResult with operation details

        Examples:
            >>> manager = PhotoFlowManager()
            >>> source = SourceInfo(
            ...     path=Path('/photos/wedding'),
            ...     name='Wedding_Smith',
            ...     date='2023-12-31'
            ... )
            >>> result = manager.create_project(source, Path('/D:'))
        """
        try:
            # Validate date is set
            if not source.date:
                raise ValueError(f"Date not set for source {source.name}")

            # Extract year from date
            year = source.date.split("-")[0]

            # Build base path: DRIVE/PROJETS_PHOTO/YEAR
            base_path = base_drive / PROJECT_ROOT_DIR / year
            base_path.mkdir(parents=True, exist_ok=True)

            # Project folder name: YYYY-MM-DD_ProjectName
            project_folder_name = f"{source.date}_{source.name}"

            # Check disk space
            source_size = estimate_directory_size(source.path)
            required_gb = source_size / (1024 ** 3) * 1.2  # 20% safety margin
            check_disk_space(base_drive, required_gb)

            # Create project structure
            logger.info(f"Creating project: {project_folder_name}")
            project_path = self.file_manager.create_project_structure(
                base_path,
                project_folder_name
            )

            # Organize files into 02_RAW
            raw_folder = project_path / "02_RAW"
            logger.info(f"Organizing files to {raw_folder}")

            copy_results = self.file_manager.organize_files(
                source.path,
                raw_folder,
                recursive=True,
                progress_callback=progress_callback
            )

            # Check if any files were copied
            success = any(r.success for r in copy_results)

            result = ProjectResult(
                source=source,
                project_path=project_path,
                copy_results=copy_results,
                success=success
            )

            logger.info(
                f"Project created: {result.files_copied} files copied, "
                f"{result.files_failed} failed, {result.files_renamed} renamed"
            )

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to create project for {source.name}: {error_msg}")

            return ProjectResult(
                source=source,
                project_path=Path(),  # Empty path
                copy_results=[],
                success=False,
                error=error_msg
            )

    def process_multiple_sources(
        self,
        sources: list[SourceInfo],
        base_drive: Path,
        auto_detect_dates: bool = True,
        progress_callback: Optional[callable] = None,
    ) -> list[ProjectResult]:
        """
        Process multiple sources and create projects.

        Args:
            sources: List of source information
            base_drive: Base drive for all projects
            auto_detect_dates: Automatically detect dates for sources without dates
            progress_callback: Optional callback for overall progress

        Returns:
            List of ProjectResult objects

        Examples:
            >>> manager = PhotoFlowManager()
            >>> sources = [
            ...     SourceInfo(Path('/photos/event1'), 'Event1'),
            ...     SourceInfo(Path('/photos/event2'), 'Event2'),
            ... ]
            >>> results = manager.process_multiple_sources(sources, Path('/D:'))
        """
        results = []

        for idx, source in enumerate(sources, 1):
            logger.info(f"Processing source {idx}/{len(sources)}: {source.name}")

            # Auto-detect date if needed
            if auto_detect_dates and not source.date:
                source.date = self.detect_date(source)

                # If still no date, skip this source
                if not source.date:
                    logger.error(f"Skipping {source.name}: no date available")
                    results.append(ProjectResult(
                        source=source,
                        project_path=Path(),
                        copy_results=[],
                        success=False,
                        error="No date available"
                    ))
                    continue

            # Create project
            result = self.create_project(source, base_drive, progress_callback)
            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        logger.info(f"Batch processing complete: {successful} successful, {failed} failed")

        return results

    def get_cache_stats(self) -> dict:
        """
        Get EXIF cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return self.exif_handler.cache_info()

    def clear_cache(self) -> None:
        """Clear EXIF cache."""
        self.exif_handler.clear_cache()
