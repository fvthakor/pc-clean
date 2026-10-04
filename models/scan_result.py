"""Scan Result and Cleanup Operation Result Models."""

from dataclasses import dataclass, field

from models.cleanup_item import CleanupCandidate


@dataclass
class ScanSummary:
    drive_letter: str
    total_space: int
    used_space: int
    free_space: int
    potential_cleanup_bytes: int = 0
    safe_cleanup_bytes: int = 0
    review_required_bytes: int = 0
    protected_bytes: int = 0
    large_files_bytes: int = 0
    leftovers_bytes: int = 0
    category_breakdown: dict[str, int] = field(default_factory=dict)
    candidates: list[CleanupCandidate] = field(default_factory=list)
    scan_duration_sec: float = 0.0


@dataclass
class CleanupOperationResult:
    category: str
    target_path: str
    cleaned_bytes: int = 0
    files_deleted: int = 0
    files_skipped: int = 0
    errors_count: int = 0
    skipped_reasons: list[str] = field(default_factory=list)
    is_success: bool = True
    quarantine_path: str | None = None
