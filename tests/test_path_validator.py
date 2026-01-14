"""Tests for path validation security."""

import os
import pytest
from pathlib import Path
import tempfile
from core.security.path_validator import (
    validate_safe_path,
    validate_filename,
    ensure_directory,
    PathTraversalError,
)


class TestValidateSafePath:
    """Test safe path validation."""
    
    def test_valid_path_within_base(self, tmp_path):
        """Test that valid path within base is accepted."""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        result = validate_safe_path(test_file, allowed_base=tmp_path)
        assert result == test_file.resolve()
    
    def test_path_traversal_blocked(self, tmp_path):
        """Test that path traversal is blocked."""
        # Try to escape tmp_path using ../
        malicious_path = tmp_path / ".." / ".." / "etc" / "passwd"
        
        with pytest.raises(PathTraversalError) as exc_info:
            validate_safe_path(malicious_path, allowed_base=tmp_path)
        assert "outside allowed directory" in str(exc_info.value)
    
    def test_absolute_path_outside_base_blocked(self, tmp_path):
        """Test that absolute path outside base is blocked."""
        # Use a more portable path for testing
        import sys
        if sys.platform == 'win32':
            outside_path = "C:\\Windows\\System32\\config"
        else:
            outside_path = "/etc/passwd"
            
        with pytest.raises(PathTraversalError):
            validate_safe_path(outside_path, allowed_base=tmp_path)
    
    def test_relative_path_converted_to_absolute(self, tmp_path):
        """Test that relative paths are converted to absolute."""
        os.chdir(tmp_path)
        result = validate_safe_path("test.txt", allowed_base=tmp_path, allow_create=True)
        assert result.is_absolute()
        assert str(tmp_path) in str(result)
    
    def test_nonexistent_path_allowed_with_allow_create(self, tmp_path):
        """Test that non-existent path is allowed with allow_create=True."""
        new_file = tmp_path / "new" / "file.txt"
        result = validate_safe_path(new_file, allowed_base=tmp_path, allow_create=True)
        assert result == new_file.resolve()
    
    def test_nonexistent_path_rejected_without_allow_create(self, tmp_path):
        """Test that non-existent path is rejected with allow_create=False."""
        new_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            validate_safe_path(new_file, allowed_base=tmp_path, allow_create=False)
    
    def test_none_allowed_base_uses_cwd(self):
        """Test that None allowed_base uses current working directory."""
        result = validate_safe_path(".", allowed_base=None)
        assert result == Path.cwd().resolve()
    
    def test_symlink_within_base_allowed(self, tmp_path):
        """Test that symlink within base is allowed."""
        target = tmp_path / "target.txt"
        target.touch()
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        
        result = validate_safe_path(link, allowed_base=tmp_path)
        # Should resolve to target
        assert result.exists()
    
    def test_symlink_outside_base_blocked(self, tmp_path):
        """Test that symlink pointing outside base is blocked."""
        # Create a symlink that points outside tmp_path
        link = tmp_path / "evil_link"
        try:
            link.symlink_to("/etc/passwd")
            
            with pytest.raises(PathTraversalError) as exc_info:
                validate_safe_path(link, allowed_base=tmp_path)
            assert "outside allowed directory" in str(exc_info.value)
        except OSError:
            # Permission denied on some systems
            pytest.skip("Cannot create symlink")


class TestValidateFilename:
    """Test filename validation."""
    
    def test_valid_filename(self):
        """Test that valid filename is accepted."""
        assert validate_filename("test.txt") == "test.txt"
        assert validate_filename("data-2024.json") == "data-2024.json"
        assert validate_filename("file_name.tar.gz") == "file_name.tar.gz"
    
    def test_empty_filename_rejected(self):
        """Test that empty filename is rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_filename("")
        assert "empty" in str(exc_info.value).lower()
    
    def test_path_separator_rejected(self):
        """Test that path separators are rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_filename("path/to/file.txt")
        assert "separator" in str(exc_info.value).lower()
        
        # Test backslash on Windows
        if os.altsep:
            with pytest.raises(ValueError):
                validate_filename("path\\to\\file.txt")
    
    def test_dot_dot_rejected(self):
        """Test that .. is rejected."""
        with pytest.raises(ValueError) as exc_info:
            validate_filename("..hidden")
        assert "dangerous" in str(exc_info.value).lower()
    
    def test_null_byte_rejected(self):
        """Test that null bytes are rejected."""
        with pytest.raises(ValueError):
            validate_filename("file\0.txt")
    
    def test_newline_rejected(self):
        """Test that newlines are rejected."""
        with pytest.raises(ValueError):
            validate_filename("file\n.txt")
        with pytest.raises(ValueError):
            validate_filename("file\r.txt")
    
    def test_reserved_windows_names_rejected(self):
        """Test that reserved Windows names are rejected."""
        reserved = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for name in reserved:
            with pytest.raises(ValueError) as exc_info:
                validate_filename(name)
            assert "reserved" in str(exc_info.value).lower()
            
            # Also test with extension
            with pytest.raises(ValueError):
                validate_filename(f"{name}.txt")
    
    def test_max_length_enforced(self):
        """Test that max length is enforced."""
        long_name = "a" * 256
        with pytest.raises(ValueError) as exc_info:
            validate_filename(long_name, max_length=255)
        assert "too long" in str(exc_info.value).lower()
    
    def test_max_length_custom(self):
        """Test that custom max length works."""
        name = "a" * 100
        # Should pass with high limit
        assert validate_filename(name, max_length=200) == name
        
        # Should fail with low limit
        with pytest.raises(ValueError):
            validate_filename(name, max_length=50)


class TestEnsureDirectory:
    """Test directory creation and validation."""
    
    def test_existing_directory_returned(self, tmp_path):
        """Test that existing directory is returned."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        
        result = ensure_directory(test_dir, allowed_base=tmp_path)
        assert result == test_dir.resolve()
        assert result.is_dir()
    
    def test_nonexistent_directory_created(self, tmp_path):
        """Test that non-existent directory is created."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        
        result = ensure_directory(new_dir, allowed_base=tmp_path)
        assert result.exists()
        assert result.is_dir()
    
    def test_path_traversal_in_directory_blocked(self, tmp_path):
        """Test that path traversal is blocked for directories."""
        malicious_dir = tmp_path / ".." / ".." / "etc"
        
        with pytest.raises(PathTraversalError):
            ensure_directory(malicious_dir, allowed_base=tmp_path)
    
    def test_file_exists_at_path_raises(self, tmp_path):
        """Test that existing file at path raises error."""
        test_file = tmp_path / "file.txt"
        test_file.touch()
        
        with pytest.raises(NotADirectoryError):
            ensure_directory(test_file, allowed_base=tmp_path)
    
    def test_directory_permissions(self, tmp_path):
        """Test that directory is created with correct permissions."""
        new_dir = tmp_path / "perms_test"
        result = ensure_directory(new_dir, allowed_base=tmp_path, mode=0o755)
        
        assert result.exists()
        # Check permissions (Unix only)
        if hasattr(os, 'stat'):
            stat = result.stat()
            # Mode includes file type bits, so mask them out
            mode = stat.st_mode & 0o777
            # On some systems, umask affects the actual mode
            assert mode & 0o755 == 0o755


class TestPathValidationIntegration:
    """Test integration scenarios."""
    
    def test_safe_file_write_workflow(self, tmp_path):
        """Test complete safe file write workflow."""
        # 1. Validate filename
        filename = validate_filename("output.json")
        
        # 2. Ensure output directory exists
        output_dir = ensure_directory(tmp_path / "outputs", allowed_base=tmp_path)
        
        # 3. Validate full path
        output_path = validate_safe_path(
            output_dir / filename,
            allowed_base=tmp_path,
            allow_create=True
        )
        
        # 4. Write file
        output_path.write_text('{"test": "data"}')
        
        # 5. Verify
        assert output_path.exists()
        assert output_path.read_text() == '{"test": "data"}'
    
    def test_nested_directory_creation(self, tmp_path):
        """Test creating deeply nested directories."""
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e"
        result = ensure_directory(deep_path, allowed_base=tmp_path)
        
        assert result.exists()
        assert result.is_dir()
        assert str(tmp_path) in str(result)
    
    def test_multiple_paths_in_same_base(self, tmp_path):
        """Test validating multiple paths in same base."""
        paths = [
            tmp_path / "file1.txt",
            tmp_path / "subdir" / "file2.txt",
            tmp_path / "another" / "nested" / "file3.txt",
        ]
        
        for path in paths:
            result = validate_safe_path(path, allowed_base=tmp_path, allow_create=True)
            assert str(tmp_path) in str(result)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_current_directory_dot(self, tmp_path):
        """Test handling of current directory (.)."""
        os.chdir(tmp_path)
        result = validate_safe_path(".", allowed_base=tmp_path)
        assert result == tmp_path.resolve()
    
    def test_parent_directory_within_base(self, tmp_path):
        """Test that parent directory within base is allowed."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        os.chdir(subdir)
        
        # Going up one level should still be within tmp_path
        result = validate_safe_path("..", allowed_base=tmp_path)
        assert result == tmp_path.resolve()
    
    def test_unicode_in_path(self, tmp_path):
        """Test Unicode characters in paths."""
        unicode_dir = tmp_path / "Привет_мир"
        result = ensure_directory(unicode_dir, allowed_base=tmp_path)
        assert result.exists()
    
    def test_special_characters_in_filename(self):
        """Test special characters in filename."""
        # These should be allowed
        assert validate_filename("file-name_123.txt")
        assert validate_filename("data (1).json")
        assert validate_filename("report [2024].pdf")
