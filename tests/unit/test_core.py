"""
Unit tests for core module.
"""

import pytest
from pathlib import Path

from photoflow.core import PhotoFlowManager, SourceInfo, ProjectResult
from photoflow.exceptions import PathValidationError


class TestSourceInfo:
    """Tests for SourceInfo dataclass."""

    def test_creation_valid(self, sample_source_dir):
        """Test creating valid SourceInfo."""
        source = SourceInfo(
            path=sample_source_dir,
            name="TestProject",
            date="2023-12-31"
        )

        assert source.path == sample_source_dir
        assert source.name == "TestProject"
        assert source.date == "2023-12-31"

    def test_creation_invalid_path(self, temp_dir):
        """Test creating SourceInfo with invalid path."""
        nonexistent = temp_dir / "does_not_exist"

        with pytest.raises(PathValidationError):
            SourceInfo(
                path=nonexistent,
                name="Test",
                date="2023-12-31"
            )

    def test_creation_without_date(self, sample_source_dir):
        """Test creating SourceInfo without date."""
        source = SourceInfo(
            path=sample_source_dir,
            name="TestProject"
        )

        assert source.date is None


class TestProjectResult:
    """Tests for ProjectResult dataclass."""

    def test_files_copied_count(self, sample_source_info):
        """Test files_copied property."""
        from photoflow.file_manager import CopyResult

        copy_results = [
            CopyResult(Path("a.jpg"), Path("dest/a.jpg"), success=True),
            CopyResult(Path("b.jpg"), Path("dest/b.jpg"), success=True),
            CopyResult(Path("c.jpg"), Path("dest/c.jpg"), success=False, error="test"),
        ]

        result = ProjectResult(
            source=sample_source_info,
            project_path=Path("/project"),
            copy_results=copy_results,
            success=True
        )

        assert result.files_copied == 2

    def test_files_failed_count(self, sample_source_info):
        """Test files_failed property."""
        from photoflow.file_manager import CopyResult

        copy_results = [
            CopyResult(Path("a.jpg"), Path("dest/a.jpg"), success=True),
            CopyResult(Path("b.jpg"), Path("dest/b.jpg"), success=False, error="test"),
            CopyResult(Path("c.jpg"), Path("dest/c.jpg"), success=False, error="test"),
        ]

        result = ProjectResult(
            source=sample_source_info,
            project_path=Path("/project"),
            copy_results=copy_results,
            success=False
        )

        assert result.files_failed == 2

    def test_files_renamed_count(self, sample_source_info):
        """Test files_renamed property."""
        from photoflow.file_manager import CopyResult

        copy_results = [
            CopyResult(Path("a.jpg"), Path("dest/a.jpg"), success=True, renamed=False),
            CopyResult(Path("b.jpg"), Path("dest/b_1.jpg"), success=True, renamed=True),
            CopyResult(Path("c.jpg"), Path("dest/c_1.jpg"), success=True, renamed=True),
        ]

        result = ProjectResult(
            source=sample_source_info,
            project_path=Path("/project"),
            copy_results=copy_results,
            success=True
        )

        assert result.files_renamed == 2


class TestPhotoFlowManager:
    """Tests for PhotoFlowManager class."""

    @pytest.fixture
    def manager(self):
        """Create PhotoFlowManager instance."""
        return PhotoFlowManager()

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.exif_handler is not None
        assert manager.file_manager is not None

    def test_create_project_success(self, manager, sample_source_info, mock_drive):
        """Test successful project creation."""
        result = manager.create_project(sample_source_info, mock_drive)

        assert result.success
        assert result.project_path.exists()
        assert result.source == sample_source_info
        assert len(result.copy_results) > 0

        # Check project structure
        assert (result.project_path / "02_RAW").exists()

    def test_create_project_without_date(self, manager, sample_source_dir, mock_drive):
        """Test project creation fails without date."""
        source = SourceInfo(
            path=sample_source_dir,
            name="TestProject",
            date=None
        )

        result = manager.create_project(source, mock_drive)

        assert not result.success
        assert result.error is not None

    def test_process_multiple_sources(self, manager, sample_source_dir, mock_drive):
        """Test processing multiple sources."""
        sources = [
            SourceInfo(sample_source_dir, "Project1", "2023-12-31"),
            SourceInfo(sample_source_dir, "Project2", "2024-01-01"),
        ]

        results = manager.process_multiple_sources(
            sources,
            mock_drive,
            auto_detect_dates=False
        )

        assert len(results) == 2
        # At least one should succeed
        assert any(r.success for r in results)

    def test_get_cache_stats(self, manager):
        """Test getting cache statistics."""
        stats = manager.get_cache_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "size" in stats
        assert "maxsize" in stats
        assert "hit_rate" in stats

    def test_clear_cache(self, manager):
        """Test clearing cache."""
        # Should not raise
        manager.clear_cache()

        stats = manager.get_cache_stats()
        assert stats["size"] == 0
