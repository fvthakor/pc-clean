"""File and Folder Item Models for Storage Analyzer."""

from dataclasses import dataclass, field
from pathlib import Path

from models.safety_result import SafetyResult


@dataclass
class FileItem:
    path: Path
    name: str
    size: int
    modified: float
    extension: str
    category: str = "File"
    safety_result: SafetyResult | None = None
    is_locked: bool = False


@dataclass
class FolderItem:
    path: Path
    name: str
    size: int = 0
    files_count: int = 0
    subfolders_count: int = 0
    modified: float = 0.0
    category: str = "Folder"
    safety_result: SafetyResult | None = None
    is_protected: bool = False
    is_expanded: bool = False
    children: list["FolderItem"] = field(default_factory=list)
