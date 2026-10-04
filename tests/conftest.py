"""Global pytest configuration and shared fixtures for PcClean test suite."""

from pathlib import Path

import pytest

from database.database import Database
from database.repositories import ProtectedPathRepository
from services.protection_service import ProtectionService
from services.safety_engine import SafetyEngine


@pytest.fixture
def temp_sandbox(tmp_path: Path) -> Path:
    """Isolated temporary sandbox folder for filesystem tests."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    return sandbox


@pytest.fixture
def test_db(temp_sandbox: Path) -> Database:
    """Isolated SQLite database in sandbox."""
    db_file = temp_sandbox / "test_pcclean.db"
    return Database(db_file)


@pytest.fixture
def protection_repo(test_db: Database) -> ProtectedPathRepository:
    return ProtectedPathRepository(test_db)


@pytest.fixture
def protection_service(protection_repo: ProtectedPathRepository) -> ProtectionService:
    return ProtectionService(protection_repo)


@pytest.fixture
def safety_engine(protection_service: ProtectionService) -> SafetyEngine:
    return SafetyEngine(protection_service)
