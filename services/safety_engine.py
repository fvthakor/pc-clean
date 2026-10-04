"""Safety Engine: The core decision authority for path safety in PcClean."""

import logging
import re
from pathlib import Path

from app.constants import PROTECTED_EXTENSIONS, PROTECTED_FILENAMES, SafetyLevel
from app.paths import (
    get_program_files,
    get_program_files_x86,
    get_system_temp_dir,
    get_user_desktop,
    get_user_documents,
    get_user_downloads,
    get_user_home,
    get_user_temp_dir,
    get_windows_dir,
)
from models.safety_result import SafetyResult
from services.protection_service import ProtectionService
from utils.filesystem import is_reparse_point

logger = logging.getLogger("PcClean.SafetyEngine")


class SafetyEngine:
    def __init__(self, protection_service: ProtectionService | None = None):
        self.protection_service = protection_service or ProtectionService()

    def evaluate_path(self, path: Path) -> SafetyResult:
        """
        Evaluate any filesystem path against comprehensive safety rules.
        Returns a SafetyResult indicating safety level, permission, and reasoning.
        """
        try:
            resolved = path.resolve()
        except Exception:
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                reason="Path resolution failed. Path may be invalid or inaccessible.",
                can_delete=False,
                confidence=1.0,
                recommendation="Do not touch this path.",
            )

        resolved_str = str(resolved).lower().rstrip("\\/")
        file_name = resolved.name.lower()
        ext = resolved.suffix.lower()

        # 1. Root drive protection (e.g. C:, D:)
        if re.match(r"^[a-z]:$", resolved_str):
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                reason="Cannot clean or delete the drive root directory directly.",
                can_delete=False,
                is_system=True,
                recommendation="Drive root is protected.",
            )

        # 2. Protected extensions (e.g. .env, .ssh, .pem, .key, .db, .sqlite)
        if ext in PROTECTED_EXTENSIONS or any(resolved_str.endswith(e) for e in PROTECTED_EXTENSIONS):
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                reason=f"Protected file extension '{ext}'. Contains credentials, keys, or database data.",
                can_delete=False,
                is_user_data=True,
                recommendation="This file contains critical security credentials or database state.",
            )

        # 3. Protected filenames
        if file_name in PROTECTED_FILENAMES:
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                reason=f"Protected critical filename '{resolved.name}'.",
                can_delete=False,
                is_user_data=True,
                recommendation="Contains authentication credentials or core configuration.",
            )

        # 4. User-marked protected paths
        if self.protection_service.is_protected(resolved):
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                reason="Location is explicitly protected by user or system safety policy.",
                can_delete=False,
                is_protected=True,
                recommendation="Remove protection in the Protected tab before attempting modifications.",
            )

        # 5. Junction / Symlink protection
        if is_reparse_point(path):
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                reason="Target is an NTFS junction or symbolic link. Deletion is blocked to prevent accidental target damage.",
                can_delete=False,
                recommendation="Unlink junctions manually if needed.",
            )

        # 6. Critical Windows System Folders
        windows_str = str(get_windows_dir()).lower().rstrip("\\/")
        if resolved_str == windows_str or (resolved_str.startswith(windows_str + "\\") and "temp" not in resolved_str):
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                reason="Windows System directory is protected. Modifying it can cause system instability.",
                can_delete=False,
                is_system=True,
                requires_admin=True,
                recommendation="System files must never be removed.",
            )

        # Windows Temp directory specifically (Safe but requires Admin)
        sys_temp = str(get_system_temp_dir()).lower().rstrip("\\/")
        if resolved_str == sys_temp or resolved_str.startswith(sys_temp + "\\"):
            return SafetyResult(
                level=SafetyLevel.SAFE,
                reason="Windows system temporary files. Safe to clean.",
                can_delete=True,
                requires_admin=True,
                is_cache=True,
                recommendation="Administrator elevation will be requested for cleaning.",
            )

        # 7. Program Files and Program Files (x86)
        pf = str(get_program_files()).lower().rstrip("\\/")
        pf86 = str(get_program_files_x86()).lower().rstrip("\\/")
        if (
            resolved_str == pf
            or resolved_str == pf86
            or resolved_str.startswith(pf + "\\")
            or resolved_str.startswith(pf86 + "\\")
        ):
            return SafetyResult(
                level=SafetyLevel.DANGEROUS,
                reason="Program Files directory contains installed applications. Use official uninstallers instead.",
                can_delete=False,
                is_system=True,
                requires_admin=True,
                recommendation="Uninstall applications via the Applications tab or Windows Settings.",
            )

        # 8. User root profile folders
        home = str(get_user_home()).lower().rstrip("\\/")
        docs = str(get_user_documents()).lower().rstrip("\\/")
        desktop = str(get_user_desktop()).lower().rstrip("\\/")
        downloads = str(get_user_downloads()).lower().rstrip("\\/")

        if resolved_str in (home, docs, desktop, downloads):
            return SafetyResult(
                level=SafetyLevel.BLOCKED,
                reason="User profile root folders (Documents, Desktop, Downloads, Home) cannot be deleted.",
                can_delete=False,
                is_user_data=True,
                recommendation="Folder is permanently protected.",
            )

        # 9. Docker Volumes Protection
        if "docker" in resolved_str and (
            "volume" in resolved_str or "wsl" in resolved_str and "docker-desktop-data" in resolved_str
        ):
            return SafetyResult(
                level=SafetyLevel.DANGEROUS,
                reason="Docker volumes may contain persistent database or application state.",
                can_delete=False,
                is_developer_data=True,
                recommendation="Manage volumes using Docker CLI or Docker Desktop.",
            )

        # 10. Browser Profiles and Credentials Protection
        if any(b in resolved_str for b in ["google\\chrome", "microsoft\\edge", "mozilla\\firefox", "brave"]):
            if any(
                p in resolved_str
                for p in ["login data", "cookies", "bookmarks", "history", "preferences", "web data", "profile "]
            ):
                return SafetyResult(
                    level=SafetyLevel.BLOCKED,
                    reason="Browser profile, bookmarks, and saved credentials must never be deleted.",
                    can_delete=False,
                    is_user_data=True,
                    recommendation="Only browser cache directories can be cleaned.",
                )

        # 11. Known Safe Caches
        if "ms-playwright" in resolved_str:
            return SafetyResult(
                level=SafetyLevel.SAFE_REDOWNLOAD,
                reason="Playwright browser binaries. Playwright will reinstall them automatically via 'npx playwright install'.",
                can_delete=True,
                is_developer_data=True,
                is_cache=True,
                recommendation="Clean if disk space is needed.",
            )

        if ".gradle\\caches" in resolved_str:
            return SafetyResult(
                level=SafetyLevel.SAFE_REDOWNLOAD,
                reason="Gradle artifact cache. Gradle will download dependencies on next build.",
                can_delete=True,
                is_developer_data=True,
                is_cache=True,
                recommendation="Clean to free space; next build will take slightly longer.",
            )

        if "npm-cache" in resolved_str or "pip\\cache" in resolved_str or "uv\\cache" in resolved_str:
            return SafetyResult(
                level=SafetyLevel.SAFE,
                reason="Developer package cache. Downloaded artifacts can be redownloaded by the package manager.",
                can_delete=True,
                is_developer_data=True,
                is_cache=True,
                recommendation="Safe to clean.",
            )

        user_temp = str(get_user_temp_dir()).lower().rstrip("\\/")
        if resolved_str == user_temp or resolved_str.startswith(user_temp + "\\"):
            return SafetyResult(
                level=SafetyLevel.SAFE,
                reason="User temporary files. Safe to clean (locked files will be skipped).",
                can_delete=True,
                is_cache=True,
                recommendation="Clean temporary files safely.",
            )

        # 12. Active developer environments
        if ("nvm" in resolved_str or "nodejs" in resolved_str) and "active" in resolved_str:
            return SafetyResult(
                level=SafetyLevel.IMPORTANT,
                reason="Active Node.js installation in use by the system.",
                can_delete=False,
                is_developer_data=True,
                recommendation="Keep active version. Switch versions with NVM first if intending to remove.",
            )

        # 13. AI Models
        if any(ai in resolved_str for ai in ["huggingface\\hub", ".ollama\\models"]):
            return SafetyResult(
                level=SafetyLevel.IMPORTANT,
                reason="AI / ML model weights. Requires re-downloading large gigabyte files if removed.",
                can_delete=False,
                is_developer_data=True,
                recommendation="Review individual models manually before removal.",
            )

        # Default fallback: REVIEW
        return SafetyResult(
            level=SafetyLevel.REVIEW,
            reason="Unclassified folder. Manual review recommended before cleaning.",
            can_delete=False,
            confidence=0.6,
            recommendation="Review contents before taking action.",
        )
