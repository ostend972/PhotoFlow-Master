"""
Pytest configuration and shared fixtures.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from PIL import Image

from photoflow import SourceInfo


@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary directory for tests.

    Args:
        tmp_path: pytest's tmp_path fixture

    Yields:
        Path to temporary directory
    """
    yield tmp_path
    # Cleanup after test
    if tmp_path.exists():
        shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def sample_image(temp_dir: Path) -> Path:
    """
    Create a sample image file without EXIF data.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path to created image
    """
    image_path = temp_dir / "test_image.jpg"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(image_path)
    return image_path


@pytest.fixture
def sample_image_with_exif(temp_dir: Path) -> Path:
    """
    Create a sample image with EXIF data.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path to created image
    """
    from PIL.ExifTags import TAGS

    image_path = temp_dir / "test_image_exif.jpg"
    img = Image.new('RGB', (100, 100), color='blue')

    # Create EXIF data
    exif_dict = {
        # DateTimeOriginal tag ID
        36867: "2023:12:31 10:30:00"
    }

    # Note: This is a simplified approach. In real tests, you might want
    # to use piexif or similar library for proper EXIF creation
    img.save(image_path, exif=img.getexif())

    return image_path


@pytest.fixture
def sample_source_dir(temp_dir: Path, sample_image: Path) -> Path:
    """
    Create a sample source directory with files.

    Args:
        temp_dir: Temporary directory
        sample_image: Sample image fixture

    Returns:
        Path to source directory
    """
    source_dir = temp_dir / "source"
    source_dir.mkdir()

    # Copy sample image
    shutil.copy(sample_image, source_dir / "photo1.jpg")
    shutil.copy(sample_image, source_dir / "photo2.jpg")

    # Create subdirectory
    subdir = source_dir / "subdir"
    subdir.mkdir()
    shutil.copy(sample_image, subdir / "photo3.jpg")

    # Create non-image file
    (source_dir / "readme.txt").write_text("Test file")

    return source_dir


@pytest.fixture
def sample_source_info(sample_source_dir: Path) -> SourceInfo:
    """
    Create a sample SourceInfo object.

    Args:
        sample_source_dir: Sample source directory

    Returns:
        SourceInfo instance
    """
    return SourceInfo(
        path=sample_source_dir,
        name="TestProject",
        date="2023-12-31"
    )


@pytest.fixture
def mock_drive(temp_dir: Path) -> Path:
    """
    Create a mock destination drive.

    Args:
        temp_dir: Temporary directory

    Returns:
        Path to mock drive
    """
    drive = temp_dir / "mock_drive"
    drive.mkdir()
    return drive
