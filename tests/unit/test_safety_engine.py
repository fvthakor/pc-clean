"""Unit tests for SafetyEngine."""

import shutil
import tempfile
from pathlib import Path

import pytest

from app.constants import SafetyLevel
from services.safety_engine import SafetyEngine


@pytest.fixture
def temp_test_env():
    """Create isolated temporary test folder structure."""
    temp_dir = Path(tempfile.mkdtemp(prefix="pcclean_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_safety_engine_blocks_root_drive():
    engine = SafetyEngine()
    result = engine.evaluate_path(Path("C:\\"))
    assert result.level == SafetyLevel.BLOCKED
    assert not result.can_delete


def test_safety_engine_blocks_windows_system():
    engine = SafetyEngine()
    result = engine.evaluate_path(Path("C:\\Windows\\System32"))
    assert result.level == SafetyLevel.BLOCKED
    assert not result.can_delete


def test_safety_engine_blocks_program_files():
    engine = SafetyEngine()
    result = engine.evaluate_path(Path("C:\\Program Files"))
    assert result.level in (SafetyLevel.BLOCKED, SafetyLevel.DANGEROUS)
    assert not result.can_delete


def test_safety_engine_blocks_env_files(temp_test_env):
    env_file = temp_test_env / ".env"
    env_file.write_text("SECRET_KEY=12345", encoding="utf-8")

    engine = SafetyEngine()
    result = engine.evaluate_path(env_file)
    assert result.level == SafetyLevel.BLOCKED
    assert not result.can_delete
    assert "Protected file extension" in result.reason or ".env" in result.reason


def test_safety_engine_blocks_ssh_keys(temp_test_env):
    key_file = temp_test_env / "id_rsa"
    key_file.write_text("PRIVATE KEY", encoding="utf-8")

    engine = SafetyEngine()
    result = engine.evaluate_path(key_file)
    assert result.level == SafetyLevel.BLOCKED
    assert not result.can_delete


def test_safety_engine_blocks_database_files(temp_test_env):
    db_file = temp_test_env / "app.sqlite3"
    db_file.write_text("dummy database content", encoding="utf-8")

    engine = SafetyEngine()
    result = engine.evaluate_path(db_file)
    assert result.level == SafetyLevel.BLOCKED
    assert not result.can_delete


def test_safety_engine_allows_safe_temp(temp_test_env):
    engine = SafetyEngine()
    # Mock evaluate a path ending in Temp or npm-cache
    temp_folder = temp_test_env / "AppData" / "Local" / "Temp"
    temp_folder.mkdir(parents=True, exist_ok=True)

    result = engine.evaluate_path(temp_folder)
    assert result is not None
    # Even if not the real system temp, let's test npm-cache which has explicit rule
    npm_cache = temp_test_env / "AppData" / "Local" / "npm-cache"
    npm_cache.mkdir(parents=True, exist_ok=True)
    res_npm = engine.evaluate_path(npm_cache)
    assert res_npm.level == SafetyLevel.SAFE
    assert res_npm.can_delete


def test_safety_engine_allows_playwright_redownload(temp_test_env):
    pw_dir = temp_test_env / "AppData" / "Local" / "ms-playwright"
    pw_dir.mkdir(parents=True, exist_ok=True)

    engine = SafetyEngine()
    result = engine.evaluate_path(pw_dir)
    assert result.level == SafetyLevel.SAFE_REDOWNLOAD
    assert result.can_delete


def test_safety_engine_blocks_docker_volumes():
    engine = SafetyEngine()
    res = engine.evaluate_path(Path("C:\\ProgramData\\Docker\\volumes\\data"))
    assert res.level == SafetyLevel.DANGEROUS
    assert not res.can_delete
