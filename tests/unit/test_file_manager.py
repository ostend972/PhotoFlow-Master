"""
Unit tests for file_manager module.
"""

import pytest
from pathlib import Path

from photoflow.file_manager import FileManager, CopyResult
from photoflow.exceptions import ProjectStructureError


class TestFileManager:
    """Tests for FileManager class."""

    @pytest.fixture
    def file_manager(self):
        """Create FileManager instance."""
        return FileManager(max_workers=2)

    def test_resolve_collision_no_collision(self, file_manager, temp_dir):
        """Test resolve_collision when no collision exists."""
        destination = temp_dir / "photo.jpg"
        result = file_manager.resolve_collision(destination)
        assert result == destination

    def test_resolve_collision_with_collision(self, file_manager, temp_dir):
        """Test resolve_collision when collision exists."""
        destination = temp_dir / "photo.jpg"
        destination.touch()  # Create file

        result = file_manager.resolve_collision(destination)
        assert result.name == "photo_1.jpg"
        assert result.parent == temp_dir

    def test_resolve_collision_multiple(self, file_manager, temp_dir):
        """Test resolve_collision with multiple collisions."""
        # Create existing files
        (temp_dir / "photo.jpg").touch()
        (temp_dir / "photo_1.jpg").touch()
        (temp_dir / "photo_2.jpg").touch()

        destination = temp_dir / "photo.jpg"
        result = file_manager.resolve_collision(destination)
        assert result.name == "photo_3.jpg"

    def test_copy_file_success(self, file_manager, temp_dir, sample_image):
        """Test successful file copy."""
        dest_dir = temp_dir / "destination"
        dest_dir.mkdir()

        result = file_manager.copy_file(sample_image, dest_dir)

        assert result.success
        assert result.source == sample_image
        assert result.destination.exists()
        assert result.destination.name == sample_image.name
        assert not result.renamed

    def test_copy_file_with_collision(self, file_manager, temp_dir, sample_image):
        """Test file copy with collision handling."""
        dest_dir = temp_dir / "destination"
        dest_dir.mkdir()

        # Copy once
        result1 = file_manager.copy_file(sample_image, dest_dir)
        assert result1.success
        assert not result1.renamed

        # Copy again (collision)
        result2 = file_manager.copy_file(sample_image, dest_dir)
        assert result2.success
        assert result2.renamed
        assert result2.destination.name != sample_image.name

    def test_copy_file_nonexistent_source(self, file_manager, temp_dir):
        """Test copy file with non-existent source."""
        nonexistent = temp_dir / "does_not_exist.jpg"
        dest_dir = temp_dir / "destination"
        dest_dir.mkdir()

        result = file_manager.copy_file(nonexistent, dest_dir)
        assert not result.success
        assert result.error is not None

    def test_organize_files(self, file_manager, sample_source_dir, temp_dir):
        """Test organizing files from source to destination."""
        dest_dir = temp_dir / "destination"
        dest_dir.mkdir()

        results = file_manager.organize_files(sample_source_dir, dest_dir)

        # Should have copied multiple files
        assert len(results) > 0
        successful = [r for r in results if r.success]
        assert len(successful) > 0

        # Check files exist
        assert len(list(dest_dir.iterdir())) > 0

    def test_create_project_structure(self, file_manager, temp_dir):
        """Test project structure creation."""
        project_path = file_manager.create_project_structure(
            temp_dir,
            "2023-12-31_TestProject"
        )

        # Check main directory exists
        assert project_path.exists()
        assert project_path.is_dir()

        # Check subdirectories
        assert (project_path / "01_PRE-PRODUCTION").exists()
        assert (project_path / "02_RAW").exists()
        assert (project_path / "03_SELECTS").exists()
        assert (project_path / "04_RETOUCHE").exists()
        assert (project_path / "05_VIDEO").exists()
        assert (project_path / "06_ADMIN").exists()

        # Check sub-subdirectories
        assert (project_path / "01_PRE-PRODUCTION" / "Moodboard").exists()
        assert (project_path / "04_RETOUCHE" / "PSD").exists()
        assert (project_path / "04_RETOUCHE" / "FINALS").exists()

    def test_create_project_structure_custom(self, file_manager, temp_dir):
        """Test project structure with custom structure."""
        custom_structure = {
            "Photos": [],
            "Videos": ["Raw", "Edited"],
        }

        project_path = file_manager.create_project_structure(
            temp_dir,
            "CustomProject",
            structure=custom_structure
        )

        assert (project_path / "Photos").exists()
        assert (project_path / "Videos").exists()
        assert (project_path / "Videos" / "Raw").exists()
        assert (project_path / "Videos" / "Edited").exists()

    def test_get_directory_stats(self, file_manager, sample_source_dir):
        """Test directory statistics."""
        stats = file_manager.get_directory_stats(sample_source_dir)

        assert "total_files" in stats
        assert "total_size_bytes" in stats
        assert "total_size_mb" in stats
        assert "total_size_gb" in stats

        assert stats["total_files"] > 0
        assert stats["total_size_bytes"] > 0
