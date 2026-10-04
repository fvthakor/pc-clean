"""Path discovery and environment resolution for WinClean."""

import os
from pathlib import Path


def get_user_home() -> Path:
    return Path(os.path.expanduser("~")).resolve()


def get_local_appdata() -> Path:
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata).resolve()
    return (get_user_home() / "AppData" / "Local").resolve()


def get_roaming_appdata() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata).resolve()
    return (get_user_home() / "AppData" / "Roaming").resolve()


def get_programdata() -> Path:
    program_data = os.environ.get("ProgramData")
    if program_data:
        return Path(program_data).resolve()
    system_drive = os.environ.get("SystemDrive", "C:")
    return Path(f"{system_drive}\\ProgramData").resolve()


def get_windows_dir() -> Path:
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if windir:
        return Path(windir).resolve()
    return Path("C:\\Windows").resolve()


def get_program_files() -> Path:
    pf = os.environ.get("ProgramFiles")
    if pf:
        return Path(pf).resolve()
    return Path("C:\\Program Files").resolve()


def get_program_files_x86() -> Path:
    pf86 = os.environ.get("ProgramFiles(x86)")
    if pf86:
        return Path(pf86).resolve()
    return Path("C:\\Program Files (x86)").resolve()


def get_user_temp_dir() -> Path:
    temp = os.environ.get("TEMP") or os.environ.get("TMP")
    if temp:
        return Path(temp).resolve()
    return (get_local_appdata() / "Temp").resolve()


def get_system_temp_dir() -> Path:
    return (get_windows_dir() / "Temp").resolve()


def get_user_documents() -> Path:
    return (get_user_home() / "Documents").resolve()


def get_user_desktop() -> Path:
    return (get_user_home() / "Desktop").resolve()


def get_user_downloads() -> Path:
    return (get_user_home() / "Downloads").resolve()


def get_pcclean_dir() -> Path:
    base = get_local_appdata() / "PcClean"
    base.mkdir(parents=True, exist_ok=True)
    return base


get_winclean_dir = get_pcclean_dir


def get_quarantine_dir() -> Path:
    q = get_pcclean_dir() / "Quarantine"
    q.mkdir(parents=True, exist_ok=True)
    return q


def get_logs_dir() -> Path:
    logs = get_pcclean_dir() / "Logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs


def get_database_path() -> Path:
    return get_pcclean_dir() / "pcclean.db"


def get_config_file_path() -> Path:
    return get_pcclean_dir() / "config.json"
