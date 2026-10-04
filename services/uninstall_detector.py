"""Uninstalled Application Leftover Detector."""

import logging
import re

from app.paths import get_local_appdata, get_programdata, get_roaming_appdata
from models.application import AppLeftoverCandidate
from services.application_service import ApplicationService
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.UninstallDetector")


class UninstallDetector:
    # Directories that must NEVER be flagged as leftovers
    KNOWN_SYSTEM_AND_DEV_FOLDERS: set[str] = {
        "microsoft",
        "windows",
        "temp",
        "packages",
        "intel",
        "nvidia",
        "amd",
        "realtek",
        "google",
        "git",
        "github",
        "docker",
        "python",
        "programs",
        "pip",
        "uv",
        "npm",
        "npm-cache",
        "nvm",
        "pnpm",
        "yarn",
        "bun",
        "android",
        "flutter",
        "pub",
        "gradle",
        ".gradle",
        "code",
        ".vscode",
        "jetbrains",
        "mozilla",
        "pcclean",
        "winclean",
        "system volume information",
        "crashdumps",
        "d3dscache",
        "comms",
        "connecteddevicesplatform",
    }

    @classmethod
    def scan_leftovers(cls) -> list[AppLeftoverCandidate]:
        """Scan AppData and ProgramData to discover uninstalled application leftovers."""
        candidates: list[AppLeftoverCandidate] = []
        installed_apps = ApplicationService.get_installed_applications()

        # Build search tokens from installed app names
        installed_tokens = set()
        for app in installed_apps:
            # tokenize app name: "Google Chrome" -> "google", "chrome"
            clean = re.sub(r"[^\w\s]", " ", app.name.lower())
            for word in clean.split():
                if len(word) >= 3:
                    installed_tokens.add(word)

        scan_roots = [get_local_appdata(), get_roaming_appdata(), get_programdata()]

        for root in scan_roots:
            if not root.exists():
                continue
            try:
                for entry in root.iterdir():
                    if not entry.is_dir() or entry.is_symlink():
                        continue
                    folder_name_lower = entry.name.lower()

                    # Skip known system and active developer ecosystems
                    if folder_name_lower in cls.KNOWN_SYSTEM_AND_DEV_FOLDERS:
                        continue

                    # Check if matches any token from installed apps
                    is_installed_match = False
                    for token in installed_tokens:
                        if token in folder_name_lower or folder_name_lower in token:
                            is_installed_match = True
                            break

                    if not is_installed_match:
                        # Check subdirectories if this is a company folder (e.g. Jio/JioSphere)
                        try:
                            subdirs = [s for s in entry.iterdir() if s.is_dir()]
                        except Exception:
                            subdirs = []

                        target_to_evaluate = entry
                        app_name = entry.name

                        if len(subdirs) == 1 and subdirs[0].name.lower() not in cls.KNOWN_SYSTEM_AND_DEV_FOLDERS:
                            # Evaluate subfolder (e.g. Jio\JioSphere)
                            target_to_evaluate = subdirs[0]
                            app_name = f"{entry.name}\\{subdirs[0].name}"

                        size, files, _ = get_dir_size_and_count(target_to_evaluate)
                        if size > 1024 * 1024:  # At least 1MB
                            # Determine confidence score
                            if files < 20 and size < 50 * 1024 * 1024:
                                confidence = 0.95
                                status = "95% LIKELY LEFTOVER"
                            elif size < 500 * 1024 * 1024:
                                confidence = 0.70
                                status = "70% LIKELY LEFTOVER"
                            else:
                                confidence = 0.40
                                status = "REVIEW REQUIRED"

                            candidates.append(
                                AppLeftoverCandidate(
                                    app_name=app_name,
                                    path=target_to_evaluate,
                                    size=size,
                                    files_count=files,
                                    confidence=confidence,
                                    status=status,
                                    reason=f"No active installed software found matching '{app_name}' in Windows registry.",
                                    last_modified=entry.stat().st_mtime,
                                )
                            )
            except Exception as e:
                logger.error(f"Error scanning root {root} for leftovers: {e}")

        # Sort largest leftovers first
        return sorted(candidates, key=lambda c: c.size, reverse=True)
