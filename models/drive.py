"""Drive Information Model."""

from dataclasses import dataclass

from app.constants import DriveType


@dataclass
class DriveInfo:
    letter: str  # e.g. "C:"
    mount_point: str  # e.g. "C:\\"
    name: str  # e.g. "Windows"
    fstype: str  # e.g. "NTFS"
    drive_type: DriveType
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent: float
    is_system: bool = False
    is_removable: bool = False

    @property
    def display_name(self) -> str:
        label = self.name if self.name else "Local Disk"
        return f"{self.letter} ({label}) - {self.drive_type.value}"
