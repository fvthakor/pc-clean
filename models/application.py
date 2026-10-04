"""Installed Application and Leftover Models."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstalledApp:
    name: str
    version: str
    publisher: str
    install_date: str
    install_location: str
    uninstall_string: str
    estimated_size: int = 0
    is_system_component: bool = False


@dataclass
class AppLeftoverCandidate:
    app_name: str
    path: Path
    size: int
    files_count: int
    confidence: float  # e.g. 0.95
    status: str  # "POSSIBLE LEFTOVER", "REVIEW"
    reason: str
    last_modified: float | None = None
