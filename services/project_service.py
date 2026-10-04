"""Project Scanner Service: Locates folder-wise developer artifacts (node_modules, venvs, build folders)."""

import logging
import os
from collections.abc import Callable
from pathlib import Path

from app.constants import SafetyLevel
from models.project_artifact import ProjectArtifact
from services.recycle_bin_service import RecycleBinService
from utils.filesystem import get_dir_size_and_count, is_reparse_point

logger = logging.getLogger("PcClean.ProjectService")

EXCLUDED_DIR_NAMES = {
    "$recycle.bin",
    "system volume information",
    "windows",
    "program files",
    "program files (x86)",
    "appdata",
    ".git",
    ".svn",
    ".idea",
    ".vscode",
}


class ProjectScannerService:
    @classmethod
    def scan_workspace_artifacts(
        cls,
        search_root: Path,
        max_depth: int = 5,
        is_cancelled: Callable[[], bool] | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[ProjectArtifact]:
        """
        Deep-scans a directory or drive for project artifacts across technologies.
        Prunes artifact sub-trees to maximize scanning speed.
        """
        results: list[ProjectArtifact] = []
        if not search_root.exists():
            return results

        root_depth = len(search_root.resolve().parts)

        for current_root, dir_names, _ in os.walk(str(search_root.resolve()), topdown=True):
            if is_cancelled and is_cancelled():
                break

            curr_p = Path(current_root)
            curr_depth = len(curr_p.parts) - root_depth
            if curr_depth > max_depth:
                dir_names.clear()
                continue

            # Filter out system and hidden ignored roots
            dir_names[:] = [d for d in dir_names if d.lower() not in EXCLUDED_DIR_NAMES and not d.startswith("$")]

            dirs_to_prune = []

            for d_name in list(dir_names):
                if is_cancelled and is_cancelled():
                    break

                target_dir = curr_p / d_name
                if is_reparse_point(target_dir):
                    dirs_to_prune.append(d_name)
                    continue

                d_lower = d_name.lower()
                matched_artifact = None

                # 1. Node.js: node_modules
                if d_lower == "node_modules":
                    recreate = "npm install"
                    if (curr_p / "yarn.lock").exists():
                        recreate = "yarn install"
                    elif (curr_p / "pnpm-lock.yaml").exists():
                        recreate = "pnpm install"
                    elif (curr_p / "bun.lockb").exists():
                        recreate = "bun install"

                    matched_artifact = ("Node.js", "node_modules", recreate)

                # 2. Python: Virtual Environments
                elif d_lower in (".venv", "venv", "env"):
                    if any(
                        (curr_p / f).exists() for f in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile")
                    ):
                        matched_artifact = ("Python", d_name, f"python -m venv {d_name}")

                # 3. Python: Bytecode and Test Caches
                elif d_lower in ("__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"):
                    matched_artifact = ("Python Cache", d_name, "Recreated on next run")

                # 4. Flutter / Dart: Build outputs
                elif d_lower in ("build", ".dart_tool") and (curr_p / "pubspec.yaml").exists():
                    matched_artifact = ("Flutter", d_name, "flutter pub get")

                # 5. Rust: Cargo target folder
                elif d_lower == "target" and (curr_p / "Cargo.toml").exists():
                    matched_artifact = ("Rust", "target", "cargo build")

                # 6. Java / Gradle: build and cache
                elif d_lower in ("build", ".gradle") and (
                    (curr_p / "build.gradle").exists()
                    or (curr_p / "build.gradle.kts").exists()
                    or (curr_p / "pom.xml").exists()
                ):
                    matched_artifact = ("Gradle", d_name, "gradle build")

                # 7. .NET / C#: bin and obj folders
                elif d_lower in ("bin", "obj") and any(curr_p.glob("*.csproj")):
                    matched_artifact = (".NET", d_name, "dotnet build")

                if matched_artifact:
                    tech, art_name, recreate_cmd = matched_artifact
                    dirs_to_prune.append(d_name)  # Don't recurse into the artifact itself

                    if progress_callback:
                        progress_callback(f"Analyzing {target_dir.name} in {curr_p.name}...")

                    try:
                        sz, fc, _ = get_dir_size_and_count(target_dir, is_cancelled=is_cancelled)
                        # Skip completely empty artifact folders
                        if sz > 0:
                            st = target_dir.stat()
                            results.append(
                                ProjectArtifact(
                                    project_name=curr_p.name,
                                    project_path=curr_p,
                                    tech=tech,
                                    artifact_name=art_name,
                                    path=target_dir,
                                    size=sz,
                                    files_count=fc,
                                    last_modified_ts=st.st_mtime,
                                    safety_level=SafetyLevel.SAFE_REDOWNLOAD,
                                    recreate_command=recreate_cmd,
                                )
                            )
                    except Exception as e:
                        logger.debug(f"Failed to calculate artifact {target_dir}: {e}")

            # Prune detected artifact folders so os.walk does not traverse inside them
            for p in dirs_to_prune:
                if p in dir_names:
                    dir_names.remove(p)

        # Sort by size descending (largest first)
        results.sort(key=lambda a: a.size, reverse=True)
        return results

    @classmethod
    def clean_artifact(cls, artifact: ProjectArtifact, use_recycle_bin: bool = True) -> bool:
        """Safely delete or recycle a project artifact folder."""
        if not artifact.path.exists():
            return True

        if use_recycle_bin:
            return RecycleBinService.send_to_bin(artifact.path)
        else:
            try:
                import shutil

                shutil.rmtree(str(artifact.path), ignore_errors=True)
                return not artifact.path.exists()
            except Exception as e:
                logger.error(f"Error removing {artifact.path}: {e}")
                return False
