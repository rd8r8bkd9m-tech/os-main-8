"""Path validation module for secure file operations.

Prevents path traversal attacks and validates file paths before operations.

Security Principles:
- Validate all file paths before use
- Prevent directory traversal (../ attacks)
- Detect symlink exploits
- Whitelist allowed directories
"""

import os
from pathlib import Path
from typing import Optional, Union


class PathTraversalError(Exception):
    """Raised when path traversal attack is detected."""
    pass


def validate_safe_path(
    path: Union[str, Path],
    allowed_base: Optional[Union[str, Path]] = None,
    allow_create: bool = True
) -> Path:
    """Validate that a path is safe to use.
    
    Args:
        path: Path to validate
        allowed_base: Base directory that path must be under (None = project root)
        allow_create: If True, allows paths that don't exist yet
        
    Returns:
        Resolved absolute path if safe
        
    Raises:
        PathTraversalError: If path is unsafe
        FileNotFoundError: If allow_create=False and path doesn't exist
        
    Example:
        >>> safe = validate_safe_path("data/output.json", "/home/user/project")
        >>> with open(safe, 'w') as f:
        ...     f.write("data")
    """
    # Convert to Path object
    path_obj = Path(path)
    
    # Get absolute path
    try:
        # Validate path exists if allow_create is False
        if not allow_create and not path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {path_obj}")

        # Resolve to get canonical path (follows symlinks, removes ..)
        abs_path = path_obj.resolve()
    except FileNotFoundError:
        # Re-raise FileNotFoundError directly without wrapping
        raise
    except (OSError, RuntimeError) as e:
        raise PathTraversalError(f"Invalid path: {e}") from e
    
    # Determine allowed base
    if allowed_base is None:
        # Default to current working directory
        allowed_base_path = Path.cwd().resolve()
    else:
        allowed_base_path = Path(allowed_base).resolve()
    
    # Check if path is under allowed base
    try:
        abs_path.relative_to(allowed_base_path)
    except ValueError:
        raise PathTraversalError(
            f"Path '{path}' is outside allowed directory '{allowed_base_path}'. "
            f"Resolved to: {abs_path}"
        )
    
    # Check for symlink exploits
    if abs_path.exists():
        # Walk up the path checking for symlinks outside allowed base
        current = abs_path
        while current != allowed_base_path:
            if current.is_symlink():
                target = current.readlink()
                if target.is_absolute():
                    # Absolute symlink - check it's under allowed base
                    try:
                        target.resolve().relative_to(allowed_base_path)
                    except ValueError:
                        raise PathTraversalError(
                            f"Symlink '{current}' points outside allowed directory: {target}"
                        )
            current = current.parent
            if current == current.parent:
                # Reached filesystem root
                break
    
    return abs_path


def validate_filename(filename: str, max_length: int = 255) -> str:
    """Validate a filename for safety.
    
    Args:
        filename: Filename to validate (not full path)
        max_length: Maximum filename length
        
    Returns:
        Validated filename
        
    Raises:
        ValueError: If filename is invalid
        
    Example:
        >>> name = validate_filename("output.json")
        >>> safe_path = validate_safe_path(f"/tmp/{name}")
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    if len(filename) > max_length:
        raise ValueError(f"Filename too long (max {max_length}): {len(filename)}")
    
    # Check for path separators
    if os.sep in filename or (os.altsep and os.altsep in filename):
        raise ValueError(f"Filename cannot contain path separators: {filename}")
    
    # Check for dangerous characters
    dangerous = ['..', '\0', '\n', '\r']
    for char in dangerous:
        if char in filename:
            raise ValueError(f"Filename contains dangerous character: {filename}")
    
    # Check for reserved Windows names
    reserved_windows = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
    }
    basename = filename.split('.')[0].upper()
    if basename in reserved_windows:
        raise ValueError(f"Filename is reserved on Windows: {filename}")
    
    return filename


def ensure_directory(
    directory: Union[str, Path],
    allowed_base: Optional[Union[str, Path]] = None,
    mode: int = 0o755
) -> Path:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path
        allowed_base: Base directory that path must be under
        mode: Directory permissions (Unix only)
        
    Returns:
        Validated directory path
        
    Raises:
        PathTraversalError: If directory path is unsafe
        PermissionError: If cannot create directory
        
    Example:
        >>> output_dir = ensure_directory("data/outputs", "/home/user/project")
        >>> with open(output_dir / "result.json", 'w') as f:
        ...     f.write("{}")
    """
    # Validate path
    dir_path = validate_safe_path(directory, allowed_base, allow_create=True)
    
    # Create if needed
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, mode=mode, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Cannot create directory '{dir_path}': {e}") from e
    elif not dir_path.is_dir():
        raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")
    
    return dir_path
