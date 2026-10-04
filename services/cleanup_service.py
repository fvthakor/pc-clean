"""Cleanup Execution Engine: Enforces SafetyEngine, executes deletions, records history."""

import logging
import shutil
from collections.abc import Callable
from pathlib import Path

from app.constants import SafetyLevel
from database.repositories import CleanupHistoryRepository
from models.cleanup_item import CleanupCandidate
from models.scan_result import CleanupOperationResult
from services.protection_service import ProtectionService
from services.quarantine_service import QuarantineService
from services.recycle_bin_service import RecycleBinService
from services.safety_engine import SafetyEngine
from utils.filesystem import is_file_locked

logger = logging.getLogger("PcClean.CleanupService")


class CleanupService:
    def __init__(
        self,
        safety_engine: SafetyEngine | None = None,
        protection_service: ProtectionService | None = None,
        history_repo: CleanupHistoryRepository | None = None,
        quarantine_service: QuarantineService | None = None,
    ):
        self.safety_engine = safety_engine or SafetyEngine()
        self.protection_service = protection_service or ProtectionService()
        self.history_repo = history_repo or CleanupHistoryRepository()
        self.quarantine_service = quarantine_service or QuarantineService()

    def execute_cleanup(
        self,
        candidates: list[CleanupCandidate],
        use_recycle_bin: bool = True,
        use_quarantine: bool = False,
        is_cancelled: Callable[[], bool] | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> CleanupOperationResult:
        """
        Execute cleanup across a list of candidates safely.
        Validates paths via SafetyEngine immediately before touching disk.
        """
        total_cleaned = 0
        total_files = 0
        total_skipped = 0
        total_errors = 0
        skipped_reasons = []

        total_count = len(candidates)

        for idx, candidate in enumerate(candidates):
            if is_cancelled and is_cancelled():
                logger.info("Cleanup cancelled by user.")
                break

            target_path = Path(candidate.path)
            if progress_callback:
                progress_callback(candidate.name, idx + 1, total_count)

            if not target_path.exists():
                continue

            # 1. Enforce SafetyEngine
            safety_res = self.safety_engine.evaluate_path(target_path)
            if not safety_res.can_delete or safety_res.level == SafetyLevel.BLOCKED:
                msg = f"{candidate.name} ({target_path}): Blocked by SafetyEngine ({safety_res.reason})"
                logger.warning(msg)
                total_skipped += 1
                skipped_reasons.append(msg)
                self.history_repo.add_entry(
                    category=candidate.category.value
                    if hasattr(candidate.category, "value")
                    else str(candidate.category),
                    path=str(target_path),
                    size_bytes=0,
                    file_count=0,
                    action="Skipped",
                    result="Blocked by SafetyEngine",
                    error_message=safety_res.reason,
                )
                continue

            # 2. Check Protection Service
            if self.protection_service.is_protected(target_path) or candidate.is_protected:
                msg = f"{candidate.name}: Path is protected"
                logger.warning(msg)
                total_skipped += 1
                skipped_reasons.append(msg)
                self.history_repo.add_entry(
                    category=candidate.category.value
                    if hasattr(candidate.category, "value")
                    else str(candidate.category),
                    path=str(target_path),
                    size_bytes=0,
                    file_count=0,
                    action="Skipped",
                    result="Protected",
                    error_message="Path is marked as Protected",
                )
                continue

            # 3. Clean files within candidate
            # If candidate represents a directory that contains files to clean (e.g. Temp directory)
            cleaned_this, files_this, skipped_this, err_this = self._clean_path(
                target_path,
                use_recycle_bin=use_recycle_bin,
                use_quarantine=use_quarantine,
                category=str(candidate.category),
                is_cancelled=is_cancelled,
            )

            total_cleaned += cleaned_this
            total_files += files_this
            total_skipped += skipped_this
            total_errors += err_this

            result_str = "Success" if err_this == 0 else f"Partial ({err_this} errors)"
            self.history_repo.add_entry(
                category=candidate.category.value if hasattr(candidate.category, "value") else str(candidate.category),
                path=str(target_path),
                size_bytes=cleaned_this,
                file_count=files_this,
                action="Cleaned",
                result=result_str,
                error_message=f"Skipped {skipped_this} locked files" if skipped_this > 0 else None,
            )

        return CleanupOperationResult(
            category="Batch Cleanup",
            target_path="Multiple",
            cleaned_bytes=total_cleaned,
            files_deleted=total_files,
            files_skipped=total_skipped,
            errors_count=total_errors,
            skipped_reasons=skipped_reasons,
            is_success=(total_errors == 0),
        )

    def _clean_path(
        self,
        path: Path,
        use_recycle_bin: bool,
        use_quarantine: bool,
        category: str,
        is_cancelled: Callable[[], bool] | None,
    ) -> tuple[int, int, int, int]:
        """
        Clean an individual file or directory tree.
        Handles locked files by skipping them.
        """
        cleaned_bytes = 0
        deleted_files = 0
        skipped_files = 0
        errors = 0

        if path.is_file():
            if is_file_locked(path):
                return 0, 0, 1, 0
            size = path.stat().st_size
            success = self._delete_or_quarantine(path, size, use_recycle_bin, use_quarantine, category)
            if success:
                return size, 1, 0, 0
            else:
                return 0, 0, 0, 1

        # Directory: Clean contents inside the directory
        try:
            entries = list(path.iterdir())
        except (PermissionError, FileNotFoundError, OSError):
            return 0, 0, 0, 1

        for child in entries:
            if is_cancelled and is_cancelled():
                break
            try:
                # Never follow symlinks/reparse points
                if child.is_symlink():
                    continue

                if child.is_file():
                    if is_file_locked(child):
                        skipped_files += 1
                        continue
                    size = child.stat().st_size
                    if self._delete_or_quarantine(child, size, use_recycle_bin, use_quarantine, category):
                        cleaned_bytes += size
                        deleted_files += 1
                    else:
                        errors += 1
                elif child.is_dir():
                    # Recursive clean for subdirectory
                    c_bytes, c_files, c_skip, c_err = self._clean_path(
                        child, use_recycle_bin, use_quarantine, category, is_cancelled
                    )
                    cleaned_bytes += c_bytes
                    deleted_files += c_files
                    skipped_files += c_skip
                    errors += c_err

                    # If subdirectory is now empty, remove directory itself
                    try:
                        if not any(child.iterdir()):
                            child.rmdir()
                    except Exception:
                        pass
            except (PermissionError, FileNotFoundError, OSError):
                errors += 1

        return cleaned_bytes, deleted_files, skipped_files, errors

    def _delete_or_quarantine(
        self, path: Path, size: int, use_recycle_bin: bool, use_quarantine: bool, category: str
    ) -> bool:
        try:
            if use_quarantine:
                return self.quarantine_service.quarantine_item(path, reason="Clean Action", category=category)
            elif use_recycle_bin:
                return RecycleBinService.send_to_bin(path)
            else:
                # Permanent deletion
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                return True
        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return False
