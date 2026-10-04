"""Python Environment, site-packages, and broken pip remnants scanner."""

import logging
import sys
import winreg
from pathlib import Path

from app.constants import SafetyLevel
from app.paths import get_local_appdata
from models.developer_tool import DeveloperTool, DevPackage
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.PythonService")


class PythonService:
    @classmethod
    def scan(cls) -> list[DeveloperTool]:
        """Scan Python installations, site-packages, and broken leftover artifacts."""
        tools: list[DeveloperTool] = []
        discovered_paths = set()

        # 1. Current executing Python
        current_py = Path(sys.executable).parent
        discovered_paths.add(str(current_py.resolve()).lower())
        cls._analyze_python_install(current_py, is_current=True, tools=tools)

        # 2. Check %LOCALAPPDATA%\Programs\Python
        py_programs = get_local_appdata() / "Programs" / "Python"
        if py_programs.exists():
            for item in py_programs.iterdir():
                if item.is_dir() and (item / "python.exe").exists():
                    p_str = str(item.resolve()).lower()
                    if p_str not in discovered_paths:
                        discovered_paths.add(p_str)
                        cls._analyze_python_install(item, is_current=False, tools=tools)

        # 3. Check Windows Registry PythonCore installations
        for root_key in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
            try:
                with winreg.OpenKey(root_key, r"Software\Python\PythonCore") as core_key:
                    num_subkeys = winreg.QueryInfoKey(core_key)[0]
                    for i in range(num_subkeys):
                        ver_str = winreg.EnumKey(core_key, i)
                        try:
                            with winreg.OpenKey(core_key, rf"{ver_str}\InstallPath") as path_key:
                                install_path_str = winreg.QueryValue(path_key, "")
                                if install_path_str:
                                    py_path = Path(install_path_str)
                                    p_str = str(py_path.resolve()).lower()
                                    if py_path.exists() and p_str not in discovered_paths:
                                        discovered_paths.add(p_str)
                                        cls._analyze_python_install(py_path, is_current=False, tools=tools)
                        except Exception:
                            continue
            except Exception:
                continue

        return tools

    @classmethod
    def _analyze_python_install(cls, py_dir: Path, is_current: bool, tools: list[DeveloperTool]) -> None:
        try:
            size, _, _ = get_dir_size_and_count(py_dir)
            version_name = py_dir.name
            packages: list[DevPackage] = []

            # Locate Lib\site-packages
            site_packages = py_dir / "Lib" / "site-packages"
            if site_packages.exists():
                for item in site_packages.iterdir():
                    if item.is_dir():
                        item_name = item.name
                        # Detect suspicious remnants like ~package or ~package.libs
                        is_broken = item_name.startswith("~") or "invalid" in item_name.lower()
                        pkg_size, _, _ = get_dir_size_and_count(item)

                        desc = "Broken pip leftover artifact (~prefix)" if is_broken else "Python library"
                        packages.append(
                            DevPackage(
                                name=item_name,
                                version="installed",
                                size=pkg_size,
                                path=item,
                                is_active=not is_broken,
                                is_broken=is_broken,
                                description=desc,
                            )
                        )

            status = "ACTIVE" if is_current else "INSTALLED"
            safety = SafetyLevel.IMPORTANT if is_current else SafetyLevel.REVIEW
            explanation = (
                f"Active Python environment running at {py_dir}. Modifying packages can disrupt scripts."
                if is_current
                else f"Installed Python runtime at {py_dir}."
            )

            # Sort packages: broken remnants first, then by size
            packages.sort(key=lambda p: (not p.is_broken, -p.size))

            tools.append(
                DeveloperTool(
                    ecosystem="Python",
                    name=f"Python ({version_name})",
                    version=version_name,
                    path=py_dir,
                    size=size,
                    status=status,
                    safety_level=safety,
                    description=f"Python Environment {version_name}",
                    is_active=is_current,
                    explanation=explanation,
                    packages=packages,
                )
            )
        except Exception as e:
            logger.error(f"Error inspecting Python directory {py_dir}: {e}")
