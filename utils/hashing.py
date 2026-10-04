"""File hashing utilities with streaming chunks and cancellation."""

import hashlib
from collections.abc import Callable
from pathlib import Path


def compute_file_hash(
    path: Path, algorithm: str = "sha256", chunk_size: int = 65536, is_cancelled: Callable[[], bool] | None = None
) -> str | None:
    """Compute cryptographic hash of a file in 64KB chunks safely."""
    if not path.is_file():
        return None
    try:
        hasher = getattr(hashlib, algorithm)()
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                if is_cancelled and is_cancelled():
                    return None
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, FileNotFoundError, OSError):
        return None


def compute_partial_hash(path: Path, bytes_to_read: int = 16384, algorithm: str = "sha256") -> str | None:
    """Compute hash of the first 16KB for rapid duplicate candidate screening."""
    if not path.is_file():
        return None
    try:
        hasher = getattr(hashlib, algorithm)()
        with open(path, "rb") as f:
            chunk = f.read(bytes_to_read)
            hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None
