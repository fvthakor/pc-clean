"""Unit tests for two-stage duplicate detection."""

import shutil
import tempfile
from pathlib import Path

import pytest

from services.duplicate_service import DuplicateService
from services.safety_engine import SafetyEngine


@pytest.fixture
def mock_duplicates_env():
    temp_dir = Path(tempfile.mkdtemp(prefix="pcclean_dup_test_"))

    # Create 2 identical files of 100 bytes
    content_dup = b"IDENTICAL_CONTENT_FOR_DUPLICATE_TEST" * 5
    (temp_dir / "orig.bin").write_bytes(content_dup)
    (temp_dir / "copy.bin").write_bytes(content_dup)

    # Create 1 file with same size but different content
    (temp_dir / "diff_content.bin").write_bytes(b"DIFFERENT_CONTENT_BUT_SAME_BYTE_SIZE" * 5)

    # Create 1 unique file
    (temp_dir / "unique.bin").write_bytes(b"UNIQUE_SIZE_FILE_12345")

    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_duplicate_service_identifies_identical_files(mock_duplicates_env):
    svc = DuplicateService(SafetyEngine())
    # Min size 1 byte to include small test files
    groups = svc.find_duplicates(mock_duplicates_env, min_size_bytes=10)

    assert len(groups) == 1
    dup_group = groups[0]
    assert len(dup_group.files) == 2
    file_names = {f.name for f in dup_group.files}
    assert file_names == {"orig.bin", "copy.bin"}
