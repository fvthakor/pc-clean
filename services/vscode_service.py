"""VS Code Extensions and Cache Scanner."""

import logging
import re
from pathlib import Path

from app.constants import SafetyLevel
from app.paths import get_roaming_appdata, get_user_home
from models.developer_tool import DeveloperTool, DevPackage
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.VSCodeService")


class VSCodeService:
    @classmethod
    def scan(cls) -> list[DeveloperTool]:
        tools: list[DeveloperTool] = []
        user_home = get_user_home()
        roaming = get_roaming_appdata()

        # 1. Extensions in ~/.vscode/extensions
        extensions_dir = user_home / ".vscode" / "extensions"
        if extensions_dir.exists():
            total_ext_size = 0
            ext_packages: list[DevPackage] = []
            grouped_exts: dict[str, list[Path]] = {}

            try:
                for ext in extensions_dir.iterdir():
                    if ext.is_dir() and not ext.name.startswith("."):
                        e_size, _, _ = get_dir_size_and_count(ext)
                        total_ext_size += e_size

                        # Group by extension identifier
                        match = re.match(r"^(.+)-(\d+\.\d+.*)$", ext.name)
                        identifier = match.group(1) if match else ext.name
                        grouped_exts.setdefault(identifier, []).append(ext)

                        ext_packages.append(
                            DevPackage(
                                name=ext.name,
                                version="extension",
                                size=e_size,
                                path=ext,
                                is_active=True,
                                description=f"VS Code extension: {ext.name}",
                            )
                        )
            except Exception as e:
                logger.error(f"Error scanning VS Code extensions: {e}")

            # Check if there are duplicate old versions
            has_duplicates = any(len(versions) > 1 for versions in grouped_exts.values())
            explanation = (
                "Active editor extensions (multiple outdated versions detected). Removing them will require reinstalling from VS Code Marketplace."
                if has_duplicates
                else "Active editor extensions. Removing them will require reinstalling from VS Code Marketplace."
            )

            tools.append(
                DeveloperTool(
                    ecosystem="VS Code",
                    name="VS Code Extensions",
                    version="Installed",
                    path=extensions_dir,
                    size=total_ext_size,
                    status="ACTIVE",
                    safety_level=SafetyLevel.IMPORTANT,
                    description=f"{len(ext_packages)} installed VS Code extensions",
                    is_active=True,
                    explanation=explanation,
                    packages=ext_packages,
                )
            )

        # 2. VS Code Caches
        cache_paths = [
            roaming / "Code" / "Cache",
            roaming / "Code" / "CachedData",
            roaming / "Code" / "Service Worker" / "CacheStorage",
        ]
        for c in cache_paths:
            if c.exists():
                c_size, _, _ = get_dir_size_and_count(c)
                if c_size > 0:
                    tools.append(
                        DeveloperTool(
                            ecosystem="VS Code",
                            name=f"VS Code {c.name}",
                            version="Cache",
                            path=c,
                            size=c_size,
                            status="CACHE",
                            safety_level=SafetyLevel.SAFE,
                            description=f"VS Code internal cache: {c.name}",
                            is_active=False,
                            explanation="Temporary cache used by VS Code runtime. Safe to clear; will regenerate on next launch.",
                            packages=[],
                        )
                    )

        return tools
