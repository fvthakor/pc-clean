"""Unified Developer Service coordinating all developer ecosystem scanners."""

import logging

from models.developer_tool import DeveloperTool
from services.ai_service import AIService
from services.android_service import AndroidService
from services.docker_service import DockerService
from services.flutter_service import FlutterService
from services.node_service import NodeService
from services.python_service import PythonService
from services.vscode_service import VSCodeService

logger = logging.getLogger("PcClean.DeveloperService")


class DeveloperService:
    @classmethod
    def scan_all(cls) -> list[DeveloperTool]:
        """Run all developer ecosystem scanners and aggregate results."""
        all_tools: list[DeveloperTool] = []
        scanners = [
            ("Node.js", NodeService.scan),
            ("Python", PythonService.scan),
            ("Android", AndroidService.scan),
            ("Flutter", FlutterService.scan),
            ("Docker", DockerService.scan),
            ("VS Code", VSCodeService.scan),
            ("AI/ML", AIService.scan),
        ]

        for name, scanner_fn in scanners:
            try:
                tools = scanner_fn()
                all_tools.extend(tools)
            except Exception as e:
                logger.error(f"Error scanning developer ecosystem {name}: {e}")

        return all_tools
