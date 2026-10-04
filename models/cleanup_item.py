"""Cleanup item models."""

from dataclasses import dataclass
from pathlib import Path

from app.constants import CleanupCategory, SafetyLevel


@dataclass
class CleanupCandidate:
    id: str
    name: str
    description: str
    path: Path
    category: CleanupCategory
    size: int
    files_count: int
    safety_level: SafetyLevel
    reason: str
    status: str = "Ready"
    is_selected: bool = False
    is_protected: bool = False
    can_recycle: bool = True
    last_modified: float | None = None
    explanation: str = ""
