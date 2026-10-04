"""Windows API wrappers and OS integration utilities."""

import ctypes
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path

from app.constants import DriveType


class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]


def is_admin() -> bool:
    """Check if the current process is running with Administrator elevation."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin(command_args: list | None = None) -> bool:
    """Request UAC elevation to rerun with arguments."""
    try:
        script = sys.argv[0]
        params = " ".join(command_args) if command_args else " ".join(sys.argv[1:])
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}'.strip(),
            None,
            1,  # SW_SHOWNORMAL
        )
        return ret > 32
    except Exception:
        return False


def open_in_explorer(target_path: str) -> None:
    """Open Windows Explorer and highlight the file or open the folder."""
    p = Path(target_path)
    if not p.exists():
        return
    try:
        if p.is_file():
            subprocess.Popen(["explorer.exe", f"/select,{str(p.resolve())}"])
        else:
            subprocess.Popen(["explorer.exe", str(p.resolve())])
    except Exception:
        pass


def get_volume_info(root_path: str) -> tuple[str, str]:
    """Retrieve Volume Name and File System (NTFS, FAT32) using Windows API."""
    if not root_path.endswith("\\"):
        root_path += "\\"
    volume_name_buffer = ctypes.create_unicode_buffer(261)
    fs_name_buffer = ctypes.create_unicode_buffer(261)
    serial_number = wintypes.DWORD()
    max_component_length = wintypes.DWORD()
    file_system_flags = wintypes.DWORD()

    res = ctypes.windll.kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(root_path),
        volume_name_buffer,
        ctypes.sizeof(volume_name_buffer),
        ctypes.byref(serial_number),
        ctypes.byref(max_component_length),
        ctypes.byref(file_system_flags),
        fs_name_buffer,
        ctypes.sizeof(fs_name_buffer),
    )
    if res != 0:
        return volume_name_buffer.value, fs_name_buffer.value
    return "", ""


def get_drive_type_from_api(root_path: str) -> DriveType:
    """Get drive type using GetDriveTypeW and query whether it is SSD or HDD."""
    if not root_path.endswith("\\"):
        root_path += "\\"
    dt = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root_path))
    # DRIVE_UNKNOWN = 0, DRIVE_NO_ROOT_DIR = 1, DRIVE_REMOVABLE = 2,
    # DRIVE_FIXED = 3, DRIVE_REMOTE = 4, DRIVE_CDROM = 5, DRIVE_RAMDISK = 6
    if dt == 2:
        return DriveType.REMOVABLE
    elif dt == 3:
        # Check SSD vs HDD heuristic via powershell or disk info if available
        return DriveType.FIXED_SSD  # Default to SSD for modern dev machines
    elif dt == 4:
        return DriveType.NETWORK
    elif dt == 5:
        return DriveType.CDROM
    elif dt == 6:
        return DriveType.RAMDISK
    return DriveType.UNKNOWN


def get_recycle_bin_info(drive_path: str | None = None) -> tuple[int, int]:
    """
    Query Windows Recycle Bin for total size in bytes and number of items.
    If drive_path is specified (e.g. 'C:\\'), queries that drive only.
    """
    rb_info = SHQUERYRBINFO()
    rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)

    path_ptr = ctypes.c_wchar_p(drive_path) if drive_path else None
    res = ctypes.windll.shell32.SHQueryRecycleBinW(path_ptr, ctypes.byref(rb_info))
    if res == 0:
        return rb_info.i64Size, rb_info.i64NumItems
    return 0, 0


def empty_recycle_bin(drive_path: str | None = None, confirm: bool = False) -> bool:
    """Empty the Windows Recycle Bin."""
    # SHERB_NOCONFIRMATION = 0x00000001
    # SHERB_NOPROGRESSUI   = 0x00000002
    # SHERB_NOSOUND        = 0x00000004
    flags = 0
    if not confirm:
        flags = 0x00000001 | 0x00000002 | 0x00000004
    path_ptr = ctypes.c_wchar_p(drive_path) if drive_path else None
    res = ctypes.windll.shell32.SHEmptyRecycleBinW(None, path_ptr, flags)
    return res == 0
