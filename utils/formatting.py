"""Formatting utilities for UI strings, badges, timestamps."""

from datetime import datetime


def format_timestamp(timestamp: float | None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format Unix timestamp or None into readable date string."""
    if not timestamp:
        return "Unknown"
    try:
        return datetime.fromtimestamp(timestamp).strftime(fmt)
    except Exception:
        return "Invalid date"


def format_confidence(confidence: float) -> str:
    """Format confidence float (0.0 to 1.0 or 0 to 100) as readable percentage."""
    if confidence <= 1.0:
        pct = confidence * 100
    else:
        pct = confidence
    return f"{pct:.0f}%"


def truncate_path(path: str, max_length: int = 50) -> str:
    """Truncate path with middle ellipsis for compact display."""
    if len(path) <= max_length:
        return path
    half = (max_length - 3) // 2
    return f"{path[:half]}...{path[-half:]}"
