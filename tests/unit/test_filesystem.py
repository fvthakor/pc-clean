"""Unit tests for filesystem utilities and traversal safety."""

from pathlib import Path

from utils.filesystem import get_dir_size_and_count, is_path_safe_child, is_reparse_point


def test_is_path_safe_child(temp_sandbox: Path):
    parent = temp_sandbox / "parent"
    parent.mkdir()
    child = parent / "sub" / "file.txt"
    child.parent.mkdir()
    child.write_text("ok", encoding="utf-8")

    outside = temp_sandbox / "outside" / "file.txt"
    outside.parent.mkdir()
    outside.write_text("evil", encoding="utf-8")

    assert is_path_safe_child(child, parent)
    assert not is_path_safe_child(outside, parent)


def test_is_reparse_point_regular_dir(temp_sandbox: Path):
    regular_dir = temp_sandbox / "regular"
    regular_dir.mkdir()
    assert not is_reparse_point(regular_dir)


def test_get_dir_size_and_count_empty(temp_sandbox: Path):
    empty = temp_sandbox / "empty"
    empty.mkdir()
    size, files, dirs = get_dir_size_and_count(empty)
    assert size == 0
    assert files == 0
    assert dirs == 0
