"""Flutter SDK and Pub cache scanner."""

import logging
import shutil
from pathlib import Path

from app.constants import SafetyLevel
from app.paths import get_local_appdata, get_user_home
from models.developer_tool import DeveloperTool
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.FlutterService")


class FlutterService:
    @classmethod
    def scan(cls) -> list[DeveloperTool]:
        tools: list[DeveloperTool] = []
        user_home = get_user_home()
        local_appdata = get_local_appdata()

        # Check Flutter SDK
        flutter_bin = shutil.which("flutter")
        flutter_sdk_paths = []
        if flutter_bin:
            try:
                flutter_sdk_paths.append(Path(flutter_bin).resolve().parent.parent)
            except Exception:
                pass

        common_flutter = [Path("C:\\src\\flutter"), user_home / "flutter", user_home / "development" / "flutter"]
        flutter_sdk_paths.extend(common_flutter)

        discovered = set()
        for sdk in flutter_sdk_paths:
            if not sdk.exists():
                continue
            s_str = str(sdk.resolve()).lower()
            if s_str in discovered:
                continue
            discovered.add(s_str)

            size, _, _ = get_dir_size_and_count(sdk)
            tools.append(
                DeveloperTool(
                    ecosystem="Flutter",
                    name="Flutter SDK",
                    version="SDK",
                    path=sdk,
                    size=size,
                    status="ACTIVE",
                    safety_level=SafetyLevel.IMPORTANT,
                    description=f"Flutter SDK at {sdk}",
                    is_active=True,
                    explanation="Flutter framework SDK. Contains engine, dart SDK, and tool binaries.",
                    packages=[],
                )
            )

        # Check Pub cache
        pub_cache_dirs = [local_appdata / "Pub" / "Cache", user_home / ".pub-cache"]
        for pc in pub_cache_dirs:
            if pc.exists() and str(pc.resolve()).lower() not in discovered:
                discovered.add(str(pc.resolve()).lower())
                size, files, _ = get_dir_size_and_count(pc)
                tools.append(
                    DeveloperTool(
                        ecosystem="Flutter",
                        name="Flutter Pub Cache",
                        version="Cache",
                        path=pc,
                        size=size,
                        status="CACHE",
                        safety_level=SafetyLevel.SAFE_REDOWNLOAD,
                        description=f"Dart & Flutter package cache at {pc}",
                        is_active=False,
                        explanation="Downloaded Dart/Flutter package archives. Can be cleared; 'flutter pub get' will re-fetch required packages.",
                        packages=[],
                    )
                )

        return tools
