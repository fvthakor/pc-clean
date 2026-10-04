"""Developer Tool Environment and Package Models."""

from dataclasses import dataclass, field
from pathlib import Path

from app.constants import SafetyLevel


@dataclass
class DevPackage:
    name: str
    version: str
    size: int
    path: Path
    is_active: bool = True
    is_broken: bool = False
    description: str = ""


@dataclass
class DeveloperTool:
    ecosystem: str  # "Node.js", "Python", "Android", "Flutter", "Docker", "VS Code", "AI/ML"
    name: str
    version: str
    path: Path
    size: int
    status: str  # "ACTIVE", "NOT ACTIVE", "IMPORTANT", "CACHE", "REVIEW", "BROKEN LEFTOVER"
    safety_level: SafetyLevel
    description: str
    is_active: bool = False
    explanation: str = ""
    packages: list[DevPackage] = field(default_factory=list)
