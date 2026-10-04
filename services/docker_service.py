"""Docker Environment, Containers, Images, and Volumes Scanner."""

import logging
import re
import shutil
import subprocess
from pathlib import Path

from app.constants import SafetyLevel
from app.paths import get_local_appdata
from models.developer_tool import DeveloperTool
from utils.size import parse_size

logger = logging.getLogger("PcClean.DockerService")


class DockerService:
    @classmethod
    def scan(cls) -> list[DeveloperTool]:
        """Scan Docker resources and WSL disk images."""
        tools: list[DeveloperTool] = []

        # 1. Inspect WSL2 Docker Desktop disk image (ext4.vhdx)
        wsl_docker_dir = get_local_appdata() / "Docker" / "wsl"
        if wsl_docker_dir.exists():
            for vhdx in wsl_docker_dir.rglob("*.vhdx"):
                try:
                    size = vhdx.stat().st_size
                    is_volume_data = "data" in vhdx.parent.name.lower() or "data" in vhdx.name.lower()
                    tools.append(
                        DeveloperTool(
                            ecosystem="Docker",
                            name=f"Docker WSL2 Virtual Disk ({vhdx.name})",
                            version="WSL2",
                            path=vhdx,
                            size=size,
                            status="ACTIVE",
                            safety_level=SafetyLevel.DANGEROUS if is_volume_data else SafetyLevel.REVIEW,
                            description=f"Docker Virtual Hard Disk: {vhdx.name}",
                            is_active=True,
                            explanation=(
                                "Docker Desktop WSL2 data disk containing container images and persistent volumes. "
                                "NEVER delete this file manually as it will corrupt Docker state."
                            ),
                            packages=[],
                        )
                    )
                except Exception:
                    pass

        # 2. Query Docker CLI only if Docker Desktop or daemon is running
        from utils.process import is_process_running

        docker_cli = shutil.which("docker")
        if docker_cli and is_process_running(["Docker Desktop.exe", "dockerd.exe"]):
            try:
                # Run `docker system df`
                res = subprocess.run(
                    [docker_cli, "system", "df"], capture_output=True, text=True, timeout=2, check=False
                )
                if res.returncode == 0:
                    lines = res.stdout.strip().splitlines()
                    # Parse rows: TYPE, TOTAL, ACTIVE, SIZE, RECLAIMABLE
                    for line in lines[1:]:
                        parts = re.split(r"\s{2,}", line.strip())
                        if len(parts) >= 4:
                            t_type = parts[0]
                            t_size_str = parts[3]
                            t_size_bytes = parse_size(t_size_str)

                            safety = SafetyLevel.REVIEW
                            explanation = ""
                            status = "ACTIVE"
                            if "Images" in t_type:
                                safety = SafetyLevel.REVIEW
                                explanation = (
                                    "Docker images cache. Unused images can be pruned with 'docker image prune'."
                                )
                            elif "Containers" in t_type:
                                safety = SafetyLevel.REVIEW
                                explanation = (
                                    "Docker containers. Stopped containers can be removed via 'docker container prune'."
                                )
                            elif "Volumes" in t_type:
                                safety = SafetyLevel.DANGEROUS
                                status = "DANGEROUS"
                                explanation = "DOCKER VOLUMES: May contain persistent databases and application state. Never delete automatically."
                            elif "Build Cache" in t_type:
                                safety = SafetyLevel.SAFE
                                status = "CACHE"
                                explanation = (
                                    "Docker build layer cache. Can be reclaimed safely with 'docker builder prune'."
                                )

                            tools.append(
                                DeveloperTool(
                                    ecosystem="Docker",
                                    name=f"Docker {t_type}",
                                    version="Live",
                                    path=Path(f"docker://{t_type.lower()}"),
                                    size=t_size_bytes,
                                    status=status,
                                    safety_level=safety,
                                    description=f"Docker {t_type} ({line})",
                                    is_active=True,
                                    explanation=explanation,
                                    packages=[],
                                )
                            )
            except Exception as e:
                logger.debug(f"Docker CLI check skipped or timed out: {e}")

        return tools
