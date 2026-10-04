"""Unit tests for ProtectionService."""

import shutil
import tempfile
from pathlib import Path

import pytest

from database.database import Database
from database.repositories import ProtectedPathRepository
from services.protection_service import ProtectionService


@pytest.fixture
def isolated_db_env():
    temp_dir = Path(tempfile.mkdtemp(prefix="pcclean_prot_test_"))
    db_path = temp_dir / "test_prot.db"
    db = Database(db_path)
    repo = ProtectedPathRepository(db)
    svc = ProtectionService(repo)
    yield svc, temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_protect_and_unprotect_path(isolated_db_env):
    svc, temp_dir = isolated_db_env
    test_folder = temp_dir / "MyValuableProject"
    test_folder.mkdir()

    # Initially not protected (unless matched by defaults)
    assert not svc.is_protected(test_folder)

    # Protect it
    success = svc.protect_path(test_folder, name="Project Alpha", reason="Active Development")
    assert success
    assert svc.is_protected(test_folder)

    # Child files inside the protected folder should also report protected!
    child_file = test_folder / "src" / "index.js"
    assert svc.is_protected(child_file)

    # Unprotect
    unprot = svc.unprotect_path(str(test_folder.resolve()))
    assert unprot
    assert not svc.is_protected(test_folder)
