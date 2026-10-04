"""Large File Finder Service."""

import logging
import os
from collections.abc import Callable
from pathlib import Path

from models.file_item import FileItem
from services.safety_engine import SafetyEngine
from utils.filesystem import is_file_locked

logger = logging.getLogger("PcClean.LargeFileService")

FILE_CATEGORIES = {
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"},
    "ISOs & Virtual Disks": {".iso", ".vhd", ".vhdx", ".vmdk", ".qcow2", ".img"},
    "Archives": {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2", ".xz", ".zst"},
    "Installers & Executables": {".exe", ".msi", ".dll", ".sys"},
    "Models & Weights": {".bin", ".safetensors", ".ckpt", ".pt", ".onnx", ".gguf"},
    "Databases": {".db", ".sqlite", ".sqlite3", ".mdf", ".ldf"},
    "Logs & Dumps": {".log", ".dmp", ".dump"},
}


class LargeFileService:
    def __init__(self, safety_engine: SafetyEngine | None = None):
        self.safety_engine = safety_engine or SafetyEngine()

    def find_large_files(
        self,
        root_path: Path,
        min_size_bytes: int = 100 * 1024 * 1024,  # default 100MB
        is_cancelled: Callable[[], bool] | None = None,
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> list[FileItem]:
        """Scan folder or drive for files exceeding min_size_bytes."""
        large_files: list[FileItem] = []
        stack = [root_path.resolve()]
        files_scanned = 0

        while stack:
            if is_cancelled and is_cancelled():
                break
            current = stack.pop()
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        if is_cancelled and is_cancelled():
                            break
                        try:
                            # Skip symlinks/junctions
                            if entry.is_symlink():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(Path(entry.path))
                            elif entry.is_file(follow_symlinks=False):
                                files_scanned += 1
                                if files_scanned % 500 == 0 and progress_callback:
                                    progress_callback(entry.path, len(large_files))

                                st = entry.stat()
                                if st.st_size >= min_size_bytes:
                                    p = Path(entry.path)
                                    ext = p.suffix.lower()
                                    cat = "Other"
                                    for c_name, exts in FILE_CATEGORIES.items():
                                        if ext in exts:
                                            cat = c_name
                                            break

                                    safety = self.safety_engine.evaluate_path(p)
                                    large_files.append(
                                        FileItem(
                                            path=p,
                                            name=p.name,
                                            size=st.st_size,
                                            modified=st.st_mtime,
                                            extension=ext,
                                            category=cat,
                                            safety_result=safety,
                                            is_locked=is_file_locked(p),
                                        )
                                    )
                        except (PermissionError, FileNotFoundError, OSError):
                            continue
            except (PermissionError, FileNotFoundError, OSError):
                continue

        return sorted(large_files, key=lambda f: f.size, reverse=True)
