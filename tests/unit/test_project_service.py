"""Tests for ProjectScannerService (node_modules, venvs, and build outputs)."""

from pathlib import Path

from services.project_service import ProjectScannerService


def test_scan_node_modules_and_venv(tmp_path: Path):
    # 1. Create mock Node.js project
    node_proj = tmp_path / "web-app"
    node_proj.mkdir()
    (node_proj / "package.json").write_text('{"name": "web-app"}', encoding="utf-8")
    nm_dir = node_proj / "node_modules"
    nm_dir.mkdir()
    (nm_dir / "pkg1").mkdir()
    (nm_dir / "pkg1" / "index.js").write_text("console.log('hello');" * 500, encoding="utf-8")

    # 2. Create mock Python project
    py_proj = tmp_path / "api-service"
    py_proj.mkdir()
    (py_proj / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    venv_dir = py_proj / ".venv"
    venv_dir.mkdir()
    (venv_dir / "pyvenv.cfg").write_text("home = /usr/bin\n" * 400, encoding="utf-8")

    # 3. Create mock Flutter project
    flutter_proj = tmp_path / "mobile-app"
    flutter_proj.mkdir()
    (flutter_proj / "pubspec.yaml").write_text("name: mobile_app\n", encoding="utf-8")
    fl_build = flutter_proj / "build"
    fl_build.mkdir()
    (fl_build / "app.apk").write_text("binary" * 1000, encoding="utf-8")

    # Run scan
    artifacts = ProjectScannerService.scan_workspace_artifacts(tmp_path, max_depth=4)

    assert len(artifacts) >= 3
    techs = {a.tech for a in artifacts}
    assert "Node.js" in techs
    assert "Python" in techs
    assert "Flutter" in techs

    # Check node_modules artifact specifics
    nm_art = next(a for a in artifacts if a.artifact_name == "node_modules")
    assert nm_art.project_name == "web-app"
    assert nm_art.recreate_command == "npm install"
    assert nm_art.size > 0


def test_clean_artifact_non_recycle(tmp_path: Path):
    proj = tmp_path / "test-clean"
    proj.mkdir()
    (proj / "package.json").write_text("{}", encoding="utf-8")
    nm = proj / "node_modules"
    nm.mkdir()
    (nm / "test.txt").write_text("data" * 1000, encoding="utf-8")

    artifacts = ProjectScannerService.scan_workspace_artifacts(tmp_path)
    assert len(artifacts) == 1

    success = ProjectScannerService.clean_artifact(artifacts[0], use_recycle_bin=False)
    assert success
    assert not nm.exists()
