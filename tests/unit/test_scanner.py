"""Unit tests for StorageScanner and size calculations."""

import shutil
import tempfile
from pathlib import Path

import pytest

from services.safety_engine import SafetyEngine
from services.storage_scanner import StorageScanner
from utils.filesystem import get_dir_size_and_count


@pytest.fixture
def mock_tree_env():
    temp_dir = Path(tempfile.mkdtemp(prefix="pcclean_tree_test_"))

    # Create dummy structure
    # root
    # ├── folder_a (2 files, 1500 bytes)
    # │   ├── file1.txt (500 bytes)
    # │   └── file2.txt (1000 bytes)
    # └── folder_b (1 file, 300 bytes)
    #     └── file3.txt (300 bytes)

    folder_a = temp_dir / "folder_a"
    folder_a.mkdir()
    (folder_a / "file1.txt").write_bytes(b"A" * 500)
    (folder_a / "file2.txt").write_bytes(b"B" * 1000)

    folder_b = temp_dir / "folder_b"
    folder_b.mkdir()
    (folder_b / "file3.txt").write_bytes(b"C" * 300)

    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_dir_size_and_count(mock_tree_env):
    size, files, dirs = get_dir_size_and_count(mock_tree_env)
    assert size == 1800
    assert files == 3
    assert dirs == 2


def test_storage_scanner_hierarchy(mock_tree_env):
    scanner = StorageScanner(SafetyEngine())
    root_item = scanner.scan_directory_tree(mock_tree_env, max_depth=2)

    assert root_item.size == 1800
    assert len(root_item.children) == 2

    # Largest folder first
    assert root_item.children[0].name == "folder_a"
    assert root_item.children[0].size == 1500

    assert root_item.children[1].name == "folder_b"
    assert root_item.children[1].size == 300
