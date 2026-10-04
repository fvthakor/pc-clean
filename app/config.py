"""Application configuration management."""

import json
import logging
from dataclasses import asdict, dataclass

from app.paths import get_config_file_path

logger = logging.getLogger("PcClean.Config")


@dataclass
class AppConfig:
    theme: str = "dark"  # "dark", "light", "system"
    default_drive: str = "C:"
    startup_scan: bool = False
    scan_hidden_files: bool = True
    scan_system_files: bool = False
    follow_symlinks: bool = False  # NEVER follow symlinks by default for safety
    scan_network_drives: bool = False
    use_recycle_bin: bool = True  # Send to recycle bin by default
    use_quarantine: bool = False  # If True, move to PcClean Quarantine
    require_confirmation: bool = True
    min_cleanup_size_bytes: int = 1024 * 1024  # 1MB
    min_large_file_mb: int = 100
    history_retention_days: int = 90
    max_scan_workers: int = 4

    @classmethod
    def load(cls) -> "AppConfig":
        path = get_config_file_path()
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                logger.error(f"Failed to load config from {path}: {e}")
        cfg = cls()
        cfg.save()
        return cfg

    def save(self) -> None:
        path = get_config_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config to {path}: {e}")
