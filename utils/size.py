"""Byte size formatting and calculation utilities."""

import re


def format_bytes(size_bytes: int | float, precision: int = 2) -> str:
    """Format bytes into human-readable string (B, KB, MB, GB, TB)."""
    if size_bytes is None or size_bytes < 0:
        return "0 B"
    size = float(size_bytes)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    if unit_index == 0:
        return f"{int(size)} B"
    return f"{size:.{precision}f} {units[unit_index]}"


def parse_size(size_str: str) -> int:
    """Parse size string like '500MB', '2.5 GB' into bytes."""
    size_str = size_str.strip().upper()
    match = re.match(r"^([\d.]+)\s*([A-Z]*)$", size_str)
    if not match:
        return 0
    val, unit = match.groups()
    try:
        val = float(val)
    except ValueError:
        return 0
    multipliers = {
        "": 1,
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024**2,
        "MB": 1024**2,
        "G": 1024**3,
        "GB": 1024**3,
        "T": 1024**4,
        "TB": 1024**4,
    }
    return int(val * multipliers.get(unit, 1))
