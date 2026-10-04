"""Android SDK, platforms, build-tools, and emulator scanner."""

import logging
import os
from pathlib import Path

from app.constants import SafetyLevel
from app.paths import get_local_appdata
from models.developer_tool import DeveloperTool, DevPackage
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.AndroidService")


class AndroidService:
    @classmethod
    def scan(cls) -> list[DeveloperTool]:
        """Scan Android SDK components."""
        tools: list[DeveloperTool] = []

        sdk_candidates = [
            get_local_appdata() / "Android" / "Sdk",
        ]
        if os.environ.get("ANDROID_HOME"):
            sdk_candidates.append(Path(os.environ["ANDROID_HOME"]))
        if os.environ.get("ANDROID_SDK_ROOT"):
            sdk_candidates.append(Path(os.environ["ANDROID_SDK_ROOT"]))

        found_sdks = set()

        for sdk in sdk_candidates:
            if not sdk.exists():
                continue
            s_str = str(sdk.resolve()).lower()
            if s_str in found_sdks:
                continue
            found_sdks.add(s_str)

            total_size, _, _ = get_dir_size_and_count(sdk)
            packages: list[DevPackage] = []

            # Sub-components: platforms, build-tools, ndk, emulator, system-images
            components = [
                "platforms",
                "build-tools",
                "ndk",
                "emulator",
                "system-images",
                "cmdline-tools",
                "platform-tools",
            ]
            for comp in components:
                comp_dir = sdk / comp
                if comp_dir.exists():
                    c_size, _, _ = get_dir_size_and_count(comp_dir)
                    packages.append(
                        DevPackage(
                            name=f"Android {comp}",
                            version=comp,
                            size=c_size,
                            path=comp_dir,
                            is_active=True,
                            description=f"Android SDK subcomponent: {comp}",
                        )
                    )

            tools.append(
                DeveloperTool(
                    ecosystem="Android",
                    name="Android SDK",
                    version="SDK",
                    path=sdk,
                    size=total_size,
                    status="ACTIVE",
                    safety_level=SafetyLevel.IMPORTANT,
                    description=f"Android SDK at {sdk}",
                    is_active=True,
                    explanation="Android SDK contains compilers, platform APIs, and emulators required for Android and Flutter builds.",
                    packages=packages,
                )
            )

        return tools
