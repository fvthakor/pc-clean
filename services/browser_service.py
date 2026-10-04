"""Browser Cache Scanner: Scans only temporary caches and explicitly protects profiles."""

import logging

from app.constants import CleanupCategory, SafetyLevel
from app.paths import get_local_appdata
from models.cleanup_item import CleanupCandidate
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.BrowserService")


class BrowserService:
    @classmethod
    def scan_caches(cls) -> list[CleanupCandidate]:
        candidates: list[CleanupCandidate] = []
        local = get_local_appdata()

        # Browser profiles cache locations
        targets = [
            # Google Chrome
            {
                "browser": "Google Chrome",
                "paths": [
                    local / "Google" / "Chrome" / "User Data" / "Default" / "Cache",
                    local / "Google" / "Chrome" / "User Data" / "Default" / "GPUCache",
                    local / "Google" / "Chrome" / "User Data" / "Default" / "Code Cache",
                    local / "Google" / "Chrome" / "User Data" / "Crashpad",
                ],
            },
            # Microsoft Edge
            {
                "browser": "Microsoft Edge",
                "paths": [
                    local / "Microsoft" / "Edge" / "User Data" / "Default" / "Cache",
                    local / "Microsoft" / "Edge" / "User Data" / "Default" / "GPUCache",
                    local / "Microsoft" / "Edge" / "User Data" / "Default" / "Code Cache",
                    local / "Microsoft" / "Edge" / "User Data" / "Crashpad",
                ],
            },
            # Brave Browser
            {
                "browser": "Brave",
                "paths": [
                    local / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "Cache",
                    local / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "GPUCache",
                    local / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "Code Cache",
                ],
            },
            # Mozilla Firefox
            {
                "browser": "Mozilla Firefox",
                "paths": [
                    local / "Mozilla" / "Firefox" / "Profiles",  # will scan cache2 inside
                ],
            },
        ]

        for b_entry in targets:
            browser_name = b_entry["browser"]
            for p in b_entry["paths"]:
                if not p.exists():
                    continue

                if browser_name == "Mozilla Firefox" and p.name == "Profiles":
                    # Look for cache2 subdirectories inside profiles
                    for prof in p.iterdir():
                        c2 = prof / "cache2"
                        if c2.exists():
                            size, files, _ = get_dir_size_and_count(c2)
                            if size > 0:
                                candidates.append(
                                    CleanupCandidate(
                                        id=f"ff_cache_{prof.name}",
                                        name=f"{browser_name} Cache ({prof.name})",
                                        description="Temporary web page and media cache.",
                                        path=c2,
                                        category=CleanupCategory.BROWSER_CACHE,
                                        size=size,
                                        files_count=files,
                                        safety_level=SafetyLevel.SAFE,
                                        reason="Web cache files. Bookmarks, logins, and history are untouched.",
                                        is_selected=True,
                                        explanation=f"{browser_name} HTTP cache. Safe to delete; website assets will re-download when browsing.",
                                    )
                                )
                    continue

                size, files, _ = get_dir_size_and_count(p)
                if size > 0:
                    candidates.append(
                        CleanupCandidate(
                            id=f"{browser_name.lower().replace(' ', '_')}_{p.name.lower()}",
                            name=f"{browser_name} {p.name}",
                            description=f"{browser_name} temporary {p.name.lower()}.",
                            path=p,
                            category=CleanupCategory.BROWSER_CACHE,
                            size=size,
                            files_count=files,
                            safety_level=SafetyLevel.SAFE,
                            reason="Web cache files. Profiles, logins, cookies, and passwords are fully preserved.",
                            is_selected=True,
                            explanation=f"{browser_name} cache. Safe to remove without affecting bookmarks or login sessions.",
                        )
                    )

        return candidates
