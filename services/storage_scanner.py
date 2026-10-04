"""TreeSize-style Storage Scanner for drives and directories."""

import logging
import os
import stat
from collections.abc import Callable
from pathlib import Path

from models.file_item import FolderItem
from services.safety_engine import SafetyEngine

logger = logging.getLogger("PcClean.StorageScanner")


class StorageScanner:
    def __init__(self, safety_engine: SafetyEngine | None = None):
        self.safety_engine = safety_engine or SafetyEngine()

    def scan_directory_tree(
        self,
        root_path: Path,
        max_depth: int = 2,
        is_cancelled: Callable[[], bool] | None = None,
        progress_callback: Callable[[str, int], None] | None = None,
    ) -> FolderItem:
        """
        Scan directory hierarchy down to max_depth for responsive TreeSize-style visualization.
        Deeper branches can be lazily expanded on demand.
        """
        resolved_root = root_path.resolve()
        safety = self.safety_engine.evaluate_path(resolved_root)

        root_item = FolderItem(
            path=resolved_root,
            name=resolved_root.name or str(resolved_root),
            safety_result=safety,
            is_protected=safety.is_protected,
        )

        self._populate_folder(
            root_item,
            current_depth=0,
            max_depth=max_depth,
            is_cancelled=is_cancelled,
            progress_callback=progress_callback,
        )
        return root_item

    def _populate_folder(
        self,
        folder_item: FolderItem,
        current_depth: int,
        max_depth: int,
        is_cancelled: Callable[[], bool] | None,
        progress_callback: Callable[[str, int], None] | None,
    ) -> None:
        if is_cancelled and is_cancelled():
            return

        if progress_callback:
            progress_callback(str(folder_item.path), folder_item.size)

        folder_size = 0
        file_count = 0
        dir_count = 0

        try:
            with os.scandir(folder_item.path) as it:
                for entry in it:
                    if is_cancelled and is_cancelled():
                        return
                    try:
                        # Skip symlinks and junctions
                        is_reparse = False
                        try:
                            st = entry.stat(follow_symlinks=False)
                            if hasattr(st, "st_file_attributes") and (
                                st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                            ):
                                is_reparse = True
                        except Exception:
                            pass

                        if is_reparse:
                            continue

                        entry_path = Path(entry.path)

                        if entry.is_dir(follow_symlinks=False):
                            dir_count += 1
                            child_safety = self.safety_engine.evaluate_path(entry_path)
                            child_item = FolderItem(
                                path=entry_path,
                                name=entry.name,
                                modified=st.st_mtime,
                                safety_result=child_safety,
                                is_protected=child_safety.is_protected,
                            )

                            if current_depth < max_depth:
                                self._populate_folder(
                                    child_item, current_depth + 1, max_depth, is_cancelled, progress_callback
                                )
                            else:
                                # Fast shallow inspection to keep UI instant; deep size calculated on expand
                                s_size = 0
                                s_files = 0
                                s_dirs = 0
                                try:
                                    with os.scandir(entry_path) as sub_it:
                                        for sub in sub_it:
                                            try:
                                                if sub.is_file(follow_symlinks=False):
                                                    s_files += 1
                                                    s_size += sub.stat().st_size
                                                elif sub.is_dir(follow_symlinks=False):
                                                    s_dirs += 1
                                            except Exception:
                                                pass
                                except Exception:
                                    pass
                                child_item.size = s_size
                                child_item.files_count = s_files
                                child_item.subfolders_count = s_dirs

                            folder_size += child_item.size
                            folder_item.children.append(child_item)
                        else:
                            file_count += 1
                            file_size = st.st_size
                            folder_size += file_size
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, OSError):
            pass

        folder_item.size = folder_size
        folder_item.files_count = file_count
        folder_item.subfolders_count = dir_count
        # Sort children largest first for TreeSize style
        folder_item.children.sort(key=lambda c: c.size, reverse=True)
