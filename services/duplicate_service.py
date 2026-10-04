"""Two-stage Duplicate File Detection Engine (Size grouping then SHA-256 streaming hashing)."""

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from models.file_item import FileItem
from services.safety_engine import SafetyEngine
from utils.hashing import compute_file_hash, compute_partial_hash

logger = logging.getLogger("PcClean.DuplicateService")


@dataclass
class DuplicateGroup:
    size_bytes: int
    hash_sha256: str
    files: list[FileItem]


class DuplicateService:
    def __init__(self, safety_engine: SafetyEngine | None = None):
        self.safety_engine = safety_engine or SafetyEngine()

    def find_duplicates(
        self,
        root_path: Path,
        min_size_bytes: int = 1024 * 1024,  # Default 1MB minimum to avoid tiny files overhead
        is_cancelled: Callable[[], bool] | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> list[DuplicateGroup]:
        """Find duplicate files in root_path using two-stage size + SHA-256 hashing."""
        # STAGE 1: Collect files grouped by size
        if progress_callback:
            progress_callback("Stage 1: Scanning files and grouping by size...")

        size_map: dict[int, list[Path]] = {}
        stack = [root_path.resolve()]

        while stack:
            if is_cancelled and is_cancelled():
                return []
            current = stack.pop()
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        if is_cancelled and is_cancelled():
                            return []
                        try:
                            if entry.is_symlink():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(Path(entry.path))
                            elif entry.is_file(follow_symlinks=False):
                                st = entry.stat()
                                if st.st_size >= min_size_bytes:
                                    size_map.setdefault(st.st_size, []).append(Path(entry.path))
                        except (PermissionError, FileNotFoundError, OSError):
                            continue
            except (PermissionError, FileNotFoundError, OSError):
                continue

        # Filter out unique sizes
        candidate_sizes = {s: paths for s, paths in size_map.items() if len(paths) > 1}
        total_candidate_groups = len(candidate_sizes)

        # STAGE 2: Hashing candidates with streaming SHA-256
        duplicate_groups: list[DuplicateGroup] = []
        processed_groups = 0

        for size_bytes, path_list in candidate_sizes.items():
            if is_cancelled and is_cancelled():
                break
            processed_groups += 1
            if progress_callback:
                progress_callback(f"Stage 2: Hashing candidates ({processed_groups}/{total_candidate_groups})...")

            # Quick partial hash check first
            partial_map: dict[str, list[Path]] = {}
            for p in path_list:
                ph = compute_partial_hash(p)
                if ph:
                    partial_map.setdefault(ph, []).append(p)

            # For matching partials, compute full SHA-256
            for _ph, p_sublist in partial_map.items():
                if len(p_sublist) > 1:
                    full_map: dict[str, list[Path]] = {}
                    for p in p_sublist:
                        full_hash = compute_file_hash(p, is_cancelled=is_cancelled)
                        if full_hash:
                            full_map.setdefault(full_hash, []).append(p)

                    for f_hash, dup_paths in full_map.items():
                        if len(dup_paths) > 1:
                            file_items = []
                            for dp in dup_paths:
                                try:
                                    st = dp.stat()
                                    safety = self.safety_engine.evaluate_path(dp)
                                    file_items.append(
                                        FileItem(
                                            path=dp,
                                            name=dp.name,
                                            size=size_bytes,
                                            modified=st.st_mtime,
                                            extension=dp.suffix.lower(),
                                            category="Duplicate",
                                            safety_result=safety,
                                        )
                                    )
                                except Exception:
                                    pass

                            duplicate_groups.append(
                                DuplicateGroup(size_bytes=size_bytes, hash_sha256=f_hash, files=file_items)
                            )

        # Sort groups with largest duplicate sizes first
        return sorted(duplicate_groups, key=lambda g: g.size_bytes * len(g.files), reverse=True)
