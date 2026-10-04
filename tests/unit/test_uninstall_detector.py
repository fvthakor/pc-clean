"""Unit tests for Uninstalled Application Leftovers detector."""

from services.uninstall_detector import UninstallDetector


def test_known_system_and_dev_folders_are_excluded():
    # Verify that system and developer folders are never considered leftovers
    excluded = UninstallDetector.KNOWN_SYSTEM_AND_DEV_FOLDERS
    assert "microsoft" in excluded
    assert "windows" in excluded
    assert "python" in excluded
    assert "npm" in excluded
    assert "docker" in excluded
    assert "android" in excluded
    assert "jetbrains" in excluded
