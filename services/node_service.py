"""Node.js and NVM Ecosystem Scanner."""

import logging
import shutil
from pathlib import Path

from app.constants import SafetyLevel
from app.paths import get_local_appdata, get_roaming_appdata, get_user_home
from models.developer_tool import DeveloperTool, DevPackage
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.NodeService")


class NodeService:
    @staticmethod
    def get_active_node_path() -> Path | None:
        """Find the currently active Node.js binary path."""
        node_bin = shutil.which("node")
        if node_bin:
            try:
                return Path(node_bin).resolve().parent
            except Exception:
                pass
        return None

    @classmethod
    def scan(cls) -> list[DeveloperTool]:
        """Scan NVM versions and global Node installations."""
        tools: list[DeveloperTool] = []
        active_path = cls.get_active_node_path()
        active_str = str(active_path).lower() if active_path else ""

        # Check NVM locations
        nvm_paths = [
            get_roaming_appdata() / "nvm",
            get_local_appdata() / "nvm",
            get_user_home() / ".nvm",
        ]

        found_versions = set()

        for nvm_dir in nvm_paths:
            if not nvm_dir.exists():
                continue

            for item in nvm_dir.iterdir():
                if item.is_dir() and (item.name.startswith("v") or item.name[0].isdigit()):
                    v_str = str(item.resolve()).lower()
                    if v_str in found_versions:
                        continue
                    found_versions.add(v_str)

                    is_active = active_path is not None and v_str == active_str
                    size, files, _ = get_dir_size_and_count(item)

                    packages: list[DevPackage] = []
                    # Scan global node_modules if present
                    global_modules = item / "node_modules"
                    if not global_modules.exists():
                        global_modules = item / "lib" / "node_modules"

                    if global_modules.exists():
                        try:
                            for pkg in global_modules.iterdir():
                                if pkg.is_dir() and not pkg.name.startswith("."):
                                    pkg_size, _, _ = get_dir_size_and_count(pkg)
                                    packages.append(
                                        DevPackage(
                                            name=pkg.name,
                                            version="installed",
                                            size=pkg_size,
                                            path=pkg,
                                            is_active=is_active,
                                            description="Global npm package",
                                        )
                                    )
                        except Exception:
                            pass

                    safety = SafetyLevel.IMPORTANT if is_active else SafetyLevel.REVIEW
                    status = "ACTIVE" if is_active else "NOT ACTIVE"
                    explanation = (
                        "Active Node.js installation managed by NVM. Required for running Node commands."
                        if is_active
                        else "Inactive Node.js version. Review if any project still requires this specific version."
                    )

                    tools.append(
                        DeveloperTool(
                            ecosystem="Node.js",
                            name=f"Node.js {item.name}",
                            version=item.name,
                            path=item,
                            size=size,
                            status=status,
                            safety_level=safety,
                            description=f"Node.js {item.name} ({status})",
                            is_active=is_active,
                            explanation=explanation,
                            packages=packages,
                        )
                    )

        # Check standalone Program Files Node.js if not in NVM
        standalone_node = Path("C:\\Program Files\\nodejs")
        if standalone_node.exists() and str(standalone_node.resolve()).lower() not in found_versions:
            size, _, _ = get_dir_size_and_count(standalone_node)
            is_active = active_path is not None and str(standalone_node.resolve()).lower() == active_str
            tools.append(
                DeveloperTool(
                    ecosystem="Node.js",
                    name="Node.js (System)",
                    version="System",
                    path=standalone_node,
                    size=size,
                    status="ACTIVE" if is_active else "INSTALLED",
                    safety_level=SafetyLevel.IMPORTANT,
                    description="System-wide Node.js installation in Program Files.",
                    is_active=is_active,
                    explanation="System Node.js installation. Managed via Windows installer.",
                    packages=[],
                )
            )

        return tools
