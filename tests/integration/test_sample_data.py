"""Tests running against sample test environment matching Requirement #62."""

import shutil
from pathlib import Path

import pytest

from app.constants import SafetyLevel
from services.protection_service import ProtectionService
from services.safety_engine import SafetyEngine


@pytest.fixture(scope="module")
def sample_test_data():
    base = Path(__file__).parent.parent / "test_data"
    base.mkdir(exist_ok=True)

    safe_cache = base / "safe_cache"
    safe_cache.mkdir(exist_ok=True)
    # Give it an npm-cache signature
    (safe_cache / "npm-cache").mkdir(exist_ok=True)
    (safe_cache / "npm-cache" / "package.tgz").write_text("tarball", encoding="utf-8")

    protected_project = base / "protected_project"
    protected_project.mkdir(exist_ok=True)
    (protected_project / "src").mkdir(exist_ok=True)
    (protected_project / "src" / "main.py").write_text("print('hello')", encoding="utf-8")

    temp_folder = base / "temp"
    temp_folder.mkdir(exist_ok=True)
    (temp_folder / "file.tmp").write_text("temporary", encoding="utf-8")

    fake_app_leftover = base / "fake_app_leftover"
    fake_app_leftover.mkdir(exist_ok=True)
    (fake_app_leftover / "settings.ini").write_text("[config]", encoding="utf-8")

    duplicate_files = base / "duplicate_files"
    duplicate_files.mkdir(exist_ok=True)
    (duplicate_files / "a.bin").write_bytes(b"SAME_BYTES")
    (duplicate_files / "b.bin").write_bytes(b"SAME_BYTES")

    dangerous = base / "dangerous"
    dangerous.mkdir(exist_ok=True)
    (dangerous / ".env").write_text("DATABASE_URL=postgres://...", encoding="utf-8")
    (dangerous / "id_rsa").write_text("PRIVATE_KEY", encoding="utf-8")

    yield base

    # Clean up test_data after tests
    shutil.rmtree(base, ignore_errors=True)


def test_sample_test_environment_evaluations(sample_test_data):
    prot_svc = ProtectionService()
    # Explicitly mark protected_project
    prot_svc.protect_path(sample_test_data / "protected_project", "Test Project", "Active Project")
    engine = SafetyEngine(prot_svc)

    # 1. safe_cache => SAFE
    npm_cache_dir = sample_test_data / "safe_cache" / "npm-cache"
    res_safe = engine.evaluate_path(npm_cache_dir)
    assert res_safe.level == SafetyLevel.SAFE
    assert res_safe.can_delete

    # 2. protected_project => BLOCKED
    res_proj = engine.evaluate_path(sample_test_data / "protected_project")
    assert res_proj.level == SafetyLevel.BLOCKED
    assert not res_proj.can_delete

    # 3. fake_app_leftover => REVIEW
    res_leftover = engine.evaluate_path(sample_test_data / "fake_app_leftover")
    assert res_leftover.level == SafetyLevel.REVIEW

    # 4. duplicate => REVIEW
    res_dup = engine.evaluate_path(sample_test_data / "duplicate_files" / "a.bin")
    assert res_dup.level in (SafetyLevel.REVIEW, SafetyLevel.SAFE)

    # 5. dangerous (.env & id_rsa) => BLOCKED
    res_env = engine.evaluate_path(sample_test_data / "dangerous" / ".env")
    assert res_env.level == SafetyLevel.BLOCKED
    assert not res_env.can_delete

    res_key = engine.evaluate_path(sample_test_data / "dangerous" / "id_rsa")
    assert res_key.level == SafetyLevel.BLOCKED
    assert not res_key.can_delete
