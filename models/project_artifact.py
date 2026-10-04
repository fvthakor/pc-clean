"""Project workspace artifact model for folder-wise developer cleaning."""

from dataclasses import dataclass
from pathlib import Path

from app.constants import SafetyLevel


@dataclass
class ProjectArtifact:
    project_name: str
    project_path: Path
    tech: str  # "Node.js", "Python", "Flutter", "Rust", "Java", ".NET"
    artifact_name: str  # "node_modules", ".venv", "build", "target", "bin", etc.
    path: Path  # Full path to artifact directory
    size: int  # Size in bytes
    files_count: int  # Total files
    last_modified_ts: float  # Timestamp of last modification
    safety_level: SafetyLevel = SafetyLevel.SAFE_REDOWNLOAD
    recreate_command: str = ""
    is_selected: bool = False

    @property
    def display_name(self) -> str:
        return f"{self.project_name} ({self.artifact_name})"
