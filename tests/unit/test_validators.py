"""
Unit tests for validators module.
"""

import pytest
from pathlib import Path

from photoflow.validators import (
    sanitize_filename,
    validate_path,
    validate_date_format,
)
from photoflow.exceptions import PathValidationError


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_basic_sanitization(self):
        """Test basic character replacement."""
        result = sanitize_filename('file/name*.txt')
        assert result == 'file_name_.txt'

    def test_multiple_invalid_chars(self):
        """Test multiple invalid characters."""
        result = sanitize_filename('a<b>c:d"e/f\\g|h?i*j')
        assert '_' in result
        assert '<' not in result
        assert '>' not in result

    def test_empty_string(self):
        """Test empty string handling."""
        result = sanitize_filename('')
        assert result == 'unnamed'

    def test_whitespace_only(self):
        """Test whitespace-only string."""
        result = sanitize_filename('   ')
        assert result == 'unnamed'

    def test_dots_stripped(self):
        """Test leading/trailing dots are removed."""
        result = sanitize_filename('...filename...')
        assert result == 'filename'

    def test_length_limit(self):
        """Test filename length is limited."""
        long_name = 'a' * 300
        result = sanitize_filename(long_name, max_length=255)
        assert len(result) == 255

    def test_valid_filename_unchanged(self):
        """Test valid filename remains unchanged."""
        valid = 'my_photo_2023.jpg'
        result = sanitize_filename(valid)
        assert result == valid


class TestValidatePath:
    """Tests for validate_path function."""

    def test_existing_path(self, temp_dir):
        """Test validation of existing path."""
        # Should not raise
        validate_path(temp_dir, must_exist=True)

    def test_nonexistent_path(self, temp_dir):
        """Test validation fails for non-existent path."""
        nonexistent = temp_dir / "does_not_exist"
        with pytest.raises(PathValidationError):
            validate_path(nonexistent, must_exist=True)

    def test_directory_validation(self, temp_dir):
        """Test directory type validation."""
        # Should not raise
        validate_path(temp_dir, must_exist=True, must_be_dir=True)

    def test_file_validation(self, sample_image):
        """Test file type validation."""
        # Should not raise
        validate_path(sample_image, must_exist=True, must_be_file=True)

    def test_directory_when_file_expected(self, temp_dir):
        """Test validation fails when directory given but file expected."""
        with pytest.raises(PathValidationError):
            validate_path(temp_dir, must_exist=True, must_be_file=True)

    def test_file_when_directory_expected(self, sample_image):
        """Test validation fails when file given but directory expected."""
        with pytest.raises(PathValidationError):
            validate_path(sample_image, must_exist=True, must_be_dir=True)


class TestValidateDateFormat:
    """Tests for validate_date_format function."""

    def test_valid_date(self):
        """Test valid date string."""
        assert validate_date_format('31-12-2023', '%d-%m-%Y')

    def test_invalid_date(self):
        """Test invalid date string."""
        assert not validate_date_format('2023-12-31', '%d-%m-%Y')

    def test_invalid_format(self):
        """Test completely wrong format."""
        assert not validate_date_format('not a date', '%d-%m-%Y')

    def test_iso_format(self):
        """Test ISO date format."""
        assert validate_date_format('2023-12-31', '%Y-%m-%d')

    def test_edge_cases(self):
        """Test edge case dates."""
        # Leap year
        assert validate_date_format('29-02-2024', '%d-%m-%Y')
        # Invalid leap year
        assert not validate_date_format('29-02-2023', '%d-%m-%Y')
        # Invalid day
        assert not validate_date_format('32-12-2023', '%d-%m-%Y')
