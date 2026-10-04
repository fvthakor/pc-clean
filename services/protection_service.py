"""Protection Service: Manages user-protected and system-protected paths."""

import logging
from pathlib import Path

from app.paths import (
    get_program_files,
    get_program_files_x86,
    get_system_temp_dir,
    get_user_desktop,
    get_user_documents,
    get_user_downloads,
    get_user_home,
    get_windows_dir,
)
from database.repositories import ProtectedPathRepository
from models.protected_path import ProtectedPath

logger = logging.getLogger("PcClean.ProtectionService")


class ProtectionService:
    def __init__(self, repo: ProtectedPathRepository | None = None):
        self.repo = repo or ProtectedPathRepository()
        self._init_default_protections()

    def _init_default_protections(self) -> None:
        """Ensure standard user project & critical locations are marked in DB if not already present."""
        defaults = [
            (str(get_user_documents()), "User Documents", "Personal documents and projects"),
            (str(get_user_desktop()), "User Desktop", "Desktop files and shortcuts"),
            (str(get_user_downloads()), "User Downloads", "Downloaded files"),
            (str(get_user_home() / ".ssh"), "SSH Keys & Config", "Cryptographic keys and host credentials"),
            (str(get_user_home() / ".gitconfig"), "Git Configuration", "User git identity and settings"),
            (str(get_windows_dir()), "Windows Operating System", "System critical directory"),
            (str(get_program_files()), "Program Files", "Installed software directory"),
            (str(get_program_files_x86()), "Program Files (x86)", "Installed 32-bit software directory"),
        ]
        existing = {p.path.lower() for p in self.repo.get_all()}
        for path_str, name, reason in defaults:
            p = Path(path_str)
            if p.exists() and path_str.lower() not in existing:
                self.repo.add(path_str, name, reason)

    def is_protected(self, path: Path) -> bool:
        """Check if path is protected either in repository or matches critical user patterns."""
        try:
            resolved = path.resolve()
            resolved_str = str(resolved).lower().rstrip("\\/")

            # Explicit exemption: System temporary directory (C:\Windows\Temp)
            # is designed for cleaning and should not be blocked by blanket C:\Windows directory protection.
            sys_temp = str(get_system_temp_dir().resolve()).lower().rstrip("\\/")
            if resolved_str == sys_temp or resolved_str.startswith(sys_temp + "\\"):
                return False

            return self.repo.is_protected(resolved_str)
        except Exception:
            return True  # Fail-safe to protected on resolution failure

    def get_all_protected(self) -> list[ProtectedPath]:
        return self.repo.get_all()

    def protect_path(self, path: Path, name: str = "", reason: str = "User Protected") -> bool:
        if not path.exists():
            return False
        resolved_str = str(path.resolve())
        item_name = name or path.name or resolved_str
        return self.repo.add(resolved_str, item_name, reason)

    def unprotect_path(self, path_or_id: str) -> bool:
        return self.repo.remove(path_or_id)
