"""
PhotoFlow Master - File Manager Module
Optimized file operations with collision handling and concurrent support.
"""

import logging
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Generator

from .constants import (
    PROJECT_STRUCTURE,
    FILE_COPY_BUFFER_SIZE,
    MAX_WORKERS,
)
from .exceptions import FileOperationError, ProjectStructureError
from .validators import validate_path, sanitize_filename

logger = logging.getLogger(__name__)


@dataclass
class CopyResult:
    """Result of a file copy operation."""
    source: Path
    destination: Path
    success: bool
    error: Optional[str] = None
    renamed: bool = False


class FileManager:
    """
    Manager for file operations with collision handling.

    Handles:
    - Smart filename collision resolution
    - Concurrent file copying
    - Project structure creation
    - Progress tracking
    """

    def __init__(self, max_workers: int = MAX_WORKERS):
        """
        Initialize file manager.

        Args:
            max_workers: Maximum number of concurrent workers for file operations
        """
        self.max_workers = max_workers

    def resolve_collision(self, destination: Path) -> Path:
        """
        Resolve filename collision by adding a counter suffix.

        Args:
            destination: Intended destination path

        Returns:
            Available path (either original or with counter suffix)

        Examples:
            >>> fm = FileManager()
            >>> fm.resolve_collision(Path('/tmp/photo.jpg'))
            Path('/tmp/photo_1.jpg')  # If photo.jpg exists
        """
        if not destination.exists():
            return destination

        counter = 1
        stem = destination.stem
        suffix = destination.suffix
        parent = destination.parent

        while True:
            new_destination = parent / f"{stem}_{counter}{suffix}"
            if not new_destination.exists():
                logger.info(
                    f"Collision resolved: {destination.name} → {new_destination.name}"
                )
                return new_destination
            counter += 1

            # Safety check to prevent infinite loops
            if counter > 9999:
                raise FileOperationError(
                    "rename",
                    destination,
                    None,
                    "Too many collisions (>9999)"
                )

    def copy_file(
        self,
        source: Path,
        destination_dir: Path,
        handle_collision: bool = True,
        preserve_metadata: bool = True,
    ) -> CopyResult:
        """
        Copy a single file with collision handling.

        Args:
            source: Source file path
            destination_dir: Destination directory
            handle_collision: Automatically handle filename collisions
            preserve_metadata: Preserve file metadata (timestamps, permissions)

        Returns:
            CopyResult object with operation details

        Raises:
            FileOperationError: If copy operation fails
        """
        try:
            # Validate source
            validate_path(source, must_exist=True, must_be_file=True, check_readable=True)

            # Prepare destination
            destination = destination_dir / source.name

            # Handle collision
            renamed = False
            if handle_collision and destination.exists():
                destination = self.resolve_collision(destination)
                renamed = True

            # Copy file
            if preserve_metadata:
                shutil.copy2(source, destination)
            else:
                shutil.copy(source, destination)

            logger.info(f"Copied: {source.name} → {destination}")

            return CopyResult(
                source=source,
                destination=destination,
                success=True,
                renamed=renamed
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to copy {source.name}: {error_msg}")

            return CopyResult(
                source=source,
                destination=destination_dir / source.name,
                success=False,
                error=error_msg
            )

    def copy_files_concurrent(
        self,
        files: list[Path],
        destination_dir: Path,
        progress_callback: Optional[Callable[[int, int, Path], None]] = None,
    ) -> list[CopyResult]:
        """
        Copy multiple files concurrently.

        Args:
            files: List of source file paths
            destination_dir: Destination directory
            progress_callback: Optional callback for progress updates
                              Signature: callback(completed, total, current_file)

        Returns:
            List of CopyResult objects

        Examples:
            >>> fm = FileManager(max_workers=4)
            >>> results = fm.copy_files_concurrent(
            ...     [Path('a.jpg'), Path('b.jpg')],
            ...     Path('/dest')
            ... )
        """
        results = []
        total = len(files)
        completed = 0

        # Create destination directory
        destination_dir.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all copy tasks
            future_to_file = {
                executor.submit(self.copy_file, file, destination_dir): file
                for file in files
            }

            # Process completed tasks
            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)
                completed += 1

                if progress_callback:
                    progress_callback(completed, total, result.source)

        # Log summary
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        renamed = sum(1 for r in results if r.renamed)

        logger.info(
            f"Copy summary: {successful}/{total} successful, "
            f"{failed} failed, {renamed} renamed"
        )

        return results

    def organize_files(
        self,
        source_dir: Path,
        destination_dir: Path,
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int, Path], None]] = None,
    ) -> list[CopyResult]:
        """
        Organize all files from source to destination.

        Args:
            source_dir: Source directory
            destination_dir: Destination directory (typically 02_RAW)
            recursive: Search recursively in source
            progress_callback: Optional progress callback

        Returns:
            List of CopyResult objects
        """
        # Collect all files
        files = list(self._iter_files(source_dir, recursive))

        if not files:
            logger.warning(f"No files found in {source_dir}")
            return []

        logger.info(f"Found {len(files)} files to organize from {source_dir}")

        # Copy concurrently
        return self.copy_files_concurrent(files, destination_dir, progress_callback)

    def _iter_files(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Generator[Path, None, None]:
        """
        Iterate over files in a directory.

        Args:
            directory: Directory to search
            recursive: Search recursively

        Yields:
            File paths
        """
        search_method = directory.rglob if recursive else directory.glob
        for item in search_method("*"):
            if item.is_file():
                yield item

    def create_project_structure(
        self,
        base_path: Path,
        project_name: str,
        structure: Optional[dict[str, list[str]]] = None
    ) -> Path:
        """
        Create project directory structure.

        Args:
            base_path: Base path where project will be created
            project_name: Name of the project folder
            structure: Optional custom structure (uses PROJECT_STRUCTURE by default)

        Returns:
            Path to created project directory

        Raises:
            ProjectStructureError: If structure creation fails

        Examples:
            >>> fm = FileManager()
            >>> project_path = fm.create_project_structure(
            ...     Path('/projects'),
            ...     '2023-12-31_Wedding'
            ... )
        """
        if structure is None:
            structure = PROJECT_STRUCTURE

        # Sanitize project name
        safe_project_name = sanitize_filename(project_name)
        project_path = base_path / safe_project_name

        try:
            # Create main project directory
            project_path.mkdir(parents=True, exist_ok=True)

            # Create subdirectories
            for folder_name, subfolders in structure.items():
                folder_path = project_path / folder_name
                folder_path.mkdir(parents=True, exist_ok=True)

                # Create sub-subdirectories
                for subfolder in subfolders:
                    (folder_path / subfolder).mkdir(parents=True, exist_ok=True)

            logger.info(f"Project structure created: {project_path}")
            return project_path

        except (OSError, PermissionError) as e:
            raise ProjectStructureError(
                f"Failed to create project structure at {project_path}: {e}"
            )

    def get_directory_stats(self, directory: Path) -> dict:
        """
        Get statistics about a directory.

        Args:
            directory: Directory to analyze

        Returns:
            Dictionary with file counts and total size
        """
        total_files = 0
        total_size = 0

        for file_path in self._iter_files(directory, recursive=True):
            try:
                total_files += 1
                total_size += file_path.stat().st_size
            except (OSError, PermissionError):
                continue

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 ** 2),
            "total_size_gb": total_size / (1024 ** 3),
        }
