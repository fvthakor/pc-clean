"""Integration tests for PcClean CLI commands."""

from pcclean.cli import run_cli


def test_cli_protected_list_returns_zero(capsys):
    ret = run_cli(["protected", "list"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Protected Paths" in captured.out


def test_cli_cleanup_preview_returns_zero(capsys):
    ret = run_cli(["cleanup", "--preview"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "CLEANUP PREVIEW" in captured.out


def test_cli_help_on_empty(capsys):
    ret = run_cli([])
    assert ret == 0
