"""Unit tests for CleanupService and safe deletion pipeline."""

import shutil
import tempfile
from pathlib import Path

import pytest

from app.constants import CleanupCategory, SafetyLevel
from database.database import Database
from database.repositories import CleanupHistoryRepository, ProtectedPathRepository, QuarantineRepository
from models.cleanup_item import CleanupCandidate
from services.cleanup_service import CleanupService
from services.protection_service import ProtectionService
from services.quarantine_service import QuarantineService
from services.safety_engine import SafetyEngine


@pytest.fixture
def cleanup_test_env():
    temp_dir = Path(tempfile.mkdtemp(prefix="pcclean_clean_test_"))
    db = Database(temp_dir / "test.db")
    prot_repo = ProtectedPathRepository(db)
    prot_svc = ProtectionService(prot_repo)
    safety_eng = SafetyEngine(prot_svc)
    hist_repo = CleanupHistoryRepository(db)
    quarantine_repo = QuarantineRepository(db)
    quarantine_svc = QuarantineService(quarantine_repo)

    clean_svc = CleanupService(
        safety_engine=safety_eng, protection_service=prot_svc, history_repo=hist_repo, quarantine_service=quarantine_svc
    )

    yield clean_svc, prot_svc, temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_cleanup_refuses_protected_candidate(cleanup_test_env):
    clean_svc, prot_svc, temp_dir = cleanup_test_env
    secret_dir = temp_dir / "ProtectedSecrets"
    secret_dir.mkdir()
    (secret_dir / "file.txt").write_text("critical data", encoding="utf-8")

    # Mark protected
    prot_svc.protect_path(secret_dir, name="Secrets", reason="User marked")

    candidate = CleanupCandidate(
        id="c1",
        name="Secrets",
        description="test",
        path=secret_dir,
        category=CleanupCategory.OTHER,
        size=100,
        files_count=1,
        safety_level=SafetyLevel.SAFE,
        reason="test",
        is_protected=True,
    )

    result = clean_svc.execute_cleanup([candidate], use_recycle_bin=False)
    # File must still exist!
    assert (secret_dir / "file.txt").exists()
    assert result.files_skipped >= 1
    assert result.files_deleted == 0


def test_quarantine_movement_and_restore(cleanup_test_env):
    clean_svc, _, temp_dir = cleanup_test_env
    junk_dir = temp_dir / "AppData" / "Local" / "npm-cache"
    junk_dir.mkdir(parents=True)
    target_file = junk_dir / "package.tgz"
    target_file.write_text("dummy package tarball", encoding="utf-8")

    q_svc = clean_svc.quarantine_service
    success = q_svc.quarantine_item(target_file, reason="Test Quarantine", category="Cache")
    assert success
    assert not target_file.exists()

    items = q_svc.get_all()
    assert len(items) >= 1
    item_id = items[0]["id"]

    # Restore item
    restored = q_svc.restore_item(item_id)
    assert restored
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "dummy package tarball"


def test_cleanup_skips_in_use_files_gracefully(cleanup_test_env):
    clean_svc, _, temp_dir = cleanup_test_env
    temp_junk = temp_dir / "UserTemp"
    temp_junk.mkdir()
    locked_file = temp_junk / "active_app.lock"
    locked_file.write_text("data" * 100, encoding="utf-8")

    # Keep file open to simulate an active browser or process holding a lock
    with open(locked_file, "r+b"):
        candidate = CleanupCandidate(
            id="c_temp",
            name="User Temp Files",
            description="temp",
            path=temp_junk,
            category=CleanupCategory.USER_TEMP,
            size=400,
            files_count=1,
            safety_level=SafetyLevel.SAFE,
            reason="temp",
        )
        result = clean_svc.execute_cleanup([candidate], use_recycle_bin=False)
        assert result.files_skipped >= 1
        assert locked_file.exists()
