"""Recycle Bin service utilizing send2trash and Windows Shell APIs."""

import logging
from pathlib import Path

import send2trash

from utils.windows import empty_recycle_bin, get_recycle_bin_info

logger = logging.getLogger("PcClean.RecycleBinService")


class RecycleBinService:
    @staticmethod
    def send_to_bin(path: Path) -> bool:
        """Send file or folder to Windows Recycle Bin."""
        try:
            if not path.exists():
                return False
            send2trash.send2trash(str(path.resolve()))
            return True
        except Exception as e:
            logger.error(f"Error sending {path} to recycle bin: {e}")
            return False

    @staticmethod
    def get_info(drive_letter: str | None = None) -> tuple[int, int]:
        """Get total size in bytes and number of items in Recycle Bin."""
        drive_path = f"{drive_letter}\\" if drive_letter else None
        return get_recycle_bin_info(drive_path)

    @staticmethod
    def empty(drive_letter: str | None = None) -> bool:
        """Empty the Windows Recycle Bin."""
        drive_path = f"{drive_letter}\\" if drive_letter else None
        return empty_recycle_bin(drive_path, confirm=False)
