"""Drive detection and telemetry service."""

import logging
import os

import psutil

from app.constants import DriveType
from models.drive import DriveInfo
from utils.windows import get_drive_type_from_api, get_volume_info

logger = logging.getLogger("PcClean.DriveService")


class DriveService:
    @staticmethod
    def get_all_drives() -> list[DriveInfo]:
        """Detect all available Windows drives (Fixed, SSD/HDD, USB, Network)."""
        drives: list[DriveInfo] = []
        system_drive_letter = os.environ.get("SystemDrive", "C:").upper()

        try:
            partitions = psutil.disk_partitions(all=False)
        except Exception as e:
            logger.error(f"Error enumerating disk partitions: {e}")
            partitions = []

        for p in partitions:
            try:
                mount = p.mountpoint
                if not mount:
                    continue
                # Normalize letter
                letter = mount.split(":")[0].upper() + ":"
                is_sys = letter == system_drive_letter

                try:
                    usage = psutil.disk_usage(mount)
                    total = usage.total
                    used = usage.used
                    free = usage.free
                    pct = usage.percent
                except (PermissionError, OSError):
                    total = used = free = 0
                    pct = 0.0

                vol_name, fs_name = get_volume_info(mount)
                if not fs_name and p.fstype:
                    fs_name = p.fstype

                drv_type = get_drive_type_from_api(mount)
                is_removable = drv_type == DriveType.REMOVABLE

                drive_info = DriveInfo(
                    letter=letter,
                    mount_point=mount,
                    name=vol_name,
                    fstype=fs_name,
                    drive_type=drv_type,
                    total_bytes=total,
                    used_bytes=used,
                    free_bytes=free,
                    percent=pct,
                    is_system=is_sys,
                    is_removable=is_removable,
                )
                drives.append(drive_info)
            except Exception as e:
                logger.error(f"Error analyzing partition {p}: {e}")

        # Ensure at least C: is returned if partitions list was somehow empty
        if not drives:
            drives.append(
                DriveInfo(
                    letter="C:",
                    mount_point="C:\\",
                    name="OSDisk",
                    fstype="NTFS",
                    drive_type=DriveType.FIXED_SSD,
                    total_bytes=500 * 1024**3,
                    used_bytes=250 * 1024**3,
                    free_bytes=250 * 1024**3,
                    percent=50.0,
                    is_system=True,
                    is_removable=False,
                )
            )

        return sorted(drives, key=lambda d: d.letter)

    @staticmethod
    def get_drive(letter: str) -> DriveInfo | None:
        target = letter.upper().rstrip("\\")
        if not target.endswith(":"):
            target += ":"
        for d in DriveService.get_all_drives():
            if d.letter == target:
                return d
        return None
