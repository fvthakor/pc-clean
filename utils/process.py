"""Process management and locked file diagnostic utilities."""

from pathlib import Path

import psutil


def is_process_running(process_names: list[str]) -> bool:
    """Check if any of the given process names (e.g. 'chrome.exe', 'code.exe') are running."""
    names_lower = {name.lower() for name in process_names}
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() in names_lower:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def get_locking_processes(file_path: Path) -> list[str]:
    """Find process names locking a specific file."""
    locking = []
    target_str = str(file_path.resolve()).lower()
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            for open_file in proc.open_files():
                if open_file.path.lower() == target_str:
                    locking.append(proc.info["name"] or f"PID {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return locking
