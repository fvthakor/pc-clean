"""Filesystem traversal, reparse point detection, size calculation, safety checks."""

import os
import stat
from collections.abc import Callable
from pathlib import Path


def is_reparse_point(path: Path) -> bool:
    """Check if the path is a symbolic link or NTFS junction/reparse point."""
    try:
        if path.is_symlink():
            return True
        st = os.lstat(str(path))
        # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        return bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False


def is_path_safe_child(child_path: Path, parent_path: Path) -> bool:
    """Verify that child_path is strictly within parent_path, guarding against path traversal."""
    try:
        resolved_child = child_path.resolve()
        resolved_parent = parent_path.resolve()
        return resolved_parent in resolved_child.parents or resolved_child == resolved_parent
    except Exception:
        return False


def is_file_locked(file_path: Path) -> bool:
    """Check if a file is currently locked/in use by another process."""
    if not file_path.exists() or not file_path.is_file():
        return False
    try:
        # Try opening with write permission (or read if only checking access)
        with open(file_path, "r+b"):
            return False
    except (OSError, PermissionError):
        return True
    except Exception:
        return False


def get_dir_size_and_count(
    dir_path: Path, follow_symlinks: bool = False, is_cancelled: Callable[[], bool] | None = None
) -> tuple[int, int, int]:
    """
    Safely compute total size in bytes, total files count, total folders count.
    Never follows reparse points unless explicitly allowed.
    Handles PermissionError and FileNotFoundError gracefully.
    """
    total_size = 0
    total_files = 0
    total_dirs = 0

    if not dir_path.exists():
        return 0, 0, 0

    stack = [dir_path]

    while stack:
        if is_cancelled and is_cancelled():
            break
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if is_cancelled and is_cancelled():
                        break
                    try:
                        # Reparse point / junction check
                        is_reparse = False
                        try:
                            st = entry.stat(follow_symlinks=False)
                            if hasattr(st, "st_file_attributes") and (
                                st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                            ):
                                is_reparse = True
                        except Exception:
                            pass

                        if entry.is_dir(follow_symlinks=follow_symlinks):
                            if is_reparse and not follow_symlinks:
                                continue
                            total_dirs += 1
                            stack.append(Path(entry.path))
                        else:
                            total_files += 1
                            total_size += entry.stat().st_size
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            continue

    return total_size, total_files, total_dirs
