# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-04

### Added
- **Core Storage Analyzer:** TreeSize/WizTree-style hierarchical disk usage explorer with visual percentage usage bars, shallow directory scans, and interactive navigation.
- **SafetyEngine & ProtectionService:**
  - Multi-tier safety levels: `SAFE`, `SAFE_REDOWNLOAD`, `REVIEW`, `IMPORTANT`, `DANGEROUS`, `BLOCKED`.
  - Exclusion of Windows root system directories (`Windows`, `System32`, `SysWOW64`, `WinSxS`, `Program Files`).
  - Strict preservation of protected developer files (`.env*`, `.ssh`, `.key`, `.pem`, `.gitconfig`, `.db`, `.sqlite*`, `.kdbx`).
  - User custom protected paths persisted in SQLite database.
- **Developer Ecosystem Cleanup:**
  - **Node.js:** npm cache, pnpm store, yarn cache, Bun cache, obsolete nvm node versions.
  - **Python:** pip cache, uv cache, pipenv/poetry cache, orphaned `.venv` scanners.
  - **Android & Mobile:** Android SDK platform tools, old build-tools, system images, Gradle cache.
  - **Flutter:** Flutter engine cache, Pub cache.
  - **Docker:** BuildKit caches, unused dangling images, exited containers, build cache pruning.
  - **AI / ML Frameworks:** Hugging Face model cache (`~/.cache/huggingface/hub`), PyTorch cache, Ollama models, Claude CLI, Codex cache.
  - **IDE & Editors:** VS Code cache, outdated extensions, JetBrains system/cache dirs.
  - **Browsers:** Google Chrome, Microsoft Edge, Mozilla Firefox cache and GPU caches.
- **Application Leftovers Detection:**
  - Detection of residual data in `%APPDATA%`, `%LOCALAPPDATA%`, and `ProgramData` from uninstalled applications.
- **Large Files & Duplicate Finder:**
  - Fast size-filtered scanning across drives.
  - Two-stage SHA-256 duplicate detection using fast header/tail byte partial hashing followed by full content verification.
- **Safety First Cleanup Execution:**
  - Two-phase interactive cleanup preview dialog with checkbox selection and risk indicators.
  - Windows Recycle Bin (`send2trash` / Windows Shell API) integration.
  - Safe Quarantine system with complete metadata and instant restore capability.
- **Reporting & Telemetry:**
  - Exportable HTML audit reports with styled tables and charts.
  - SQLite persistent cleanup and scan history tracking.
- **Dual User Interface:**
  - Modern PySide6 dark-first desktop GUI with custom SVG icons, responsive command panel, and real-time scan progress.
  - Full CLI interface via `python -m pcclean` with subcommands: `scan`, `clean`, `report`, `protected`, `quarantine`.
- **Packaging & Deployment:**
  - PyInstaller spec configuration (`PcClean.spec`) generating standalone `PcClean.exe`.
  - Inno Setup installer script (`installer.iss`) for single-click Windows installation with uninstall cleanup.
  - Cross-platform CI/CD with GitHub Actions (`tests.yml`, `lint.yml`, `build.yml`).
