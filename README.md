# PcClean 🧹

[![Tests](https://github.com/fvthakor/pc-clean/actions/workflows/tests.yml/badge.svg)](https://github.com/fvthakor/pc-clean/actions/workflows/tests.yml)
[![Lint](https://github.com/fvthakor/pc-clean/actions/workflows/lint.yml/badge.svg)](https://github.com/fvthakor/pc-clean/actions/workflows/lint.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![Platform Windows](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6.svg)](https://microsoft.com/windows)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Developer-Focused Windows Disk Cleanup, Storage Analyzer, Cache Manager & Safe Junk Removal Utility**

PcClean is a modern desktop suite that bridges the gap between **TreeSize / WizTree**, **BleachBit**, and an intelligent **Developer Environment Manager**. Built specifically for software engineers, data scientists, and power users on Windows.

---

## 📚 Documentation & Governance

- 🏗️ **[Architecture & System Design](docs/architecture.md)** — Architectural tiers, scanner services, threading model.
- 🛡️ **[Safety Engine Specification](docs/safety-engine.md)** — Classification levels, hardcoded blacklists, and quarantine vault.
- 💻 **[Developer Setup Guide](docs/development.md)** — Virtual environment, local execution, testing, and debugging.
- 📦 **[Packaging & Release Guide](docs/release.md)** — PyInstaller binary compilation and Inno Setup installer.
- 🤝 **[Contributing Guidelines](CONTRIBUTING.md)** — Pull request workflow, branch naming, and testing standards.
- 🔒 **[Security Policy](SECURITY.md)** — Responsible vulnerability disclosure policy.
- 📜 **[Changelog](CHANGELOG.md)** — Detailed version history and release notes.

---

## 🛡️ Safety First Architecture

PcClean follows a strict **"SHOW FIRST, EXPLAIN SECOND, CLEAN LAST"** philosophy:

- **Central Safety Engine (`SafetyEngine`)**: Every filesystem path is evaluated through strict deterministic safety classifications (`SAFE`, `SAFE_REDOWNLOAD`, `REVIEW`, `IMPORTANT`, `DANGEROUS`, `BLOCKED`).
- **Zero Silent Deletions**: Every operation requires user confirmation and displays a detailed preview of paths, file counts, and reclaimed gigabytes.
- **Permanent Protection Rules**:
  - `C:\Windows`, `System32`, `Program Files`, and system partitions are hard-blocked.
  - Credential files (`.env`, `.env.*`, `.ssh`, `id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `*.pfx`) can **never** be cleaned by automated rules.
  - Databases (`*.db`, `*.sqlite`, `*.sqlite3`) are blocked from automated cleanup.
  - Docker persistent volumes are flagged as `DANGEROUS` and blocked from automatic deletion.
  - Active Node.js and active Python runtime installations are protected.
  - Browser user profiles, logins, cookies, and bookmarks are strictly shielded; only temporary rendering caches are targeted.
- **Recycle Bin & Quarantine by Default**: Files default to the Windows Recycle Bin or PcClean Quarantine (`%LOCALAPPDATA%\PcClean\Quarantine`) with full metadata for 1-click restoration.
- **Symlink & Junction Immunity**: Never follows reparse points, NTFS junctions, or symlinks by default, guarding against directory traversal attacks and infinite loops.
- **Locked File Resiliency**: Running process locks are gracefully skipped and reported without interrupting or crashing operations.

---

## ⚡ Developer Ecosystems Supported

PcClean natively detects and analyzes:

| Ecosystem | Detected Components | Safety Level |
| :--- | :--- | :--- |
| **Node.js & NVM** | NVM versions, active Node runtime, global packages (n8n, opencode-ai, etc.) | Active: `IMPORTANT`, Old: `REVIEW` |
| **Package Caches** | npm cache, pnpm store, Yarn cache, Bun cache | `SAFE` |
| **Python & pip** | Active Python environments, site-packages, broken pip remnants (`~package`) | Active: `IMPORTANT`, Remnants: `REVIEW` |
| **Python Caches** | pip wheel/HTTP cache, Astral uv cache | `SAFE` |
| **Android SDK** | Platforms, build-tools, emulator, system-images, NDK | `IMPORTANT` |
| **Flutter & Dart** | Flutter SDK, Pub package cache (`.pub-cache`, `Pub/Cache`) | `SAFE_REDOWNLOAD` |
| **Gradle** | `.gradle\caches`, `.gradle\wrapper\dists` | `SAFE_REDOWNLOAD` |
| **Playwright** | Headless browser binaries (Chromium, Firefox, WebKit in `ms-playwright`) | `SAFE_REDOWNLOAD` |
| **Docker** | Images, containers, build cache, WSL2 `.vhdx` disks, volumes | Volumes: `DANGEROUS`, Cache: `SAFE` |
| **VS Code** | Extensions, duplicate old versions, internal caches (`CachedData`, `Service Worker`) | Cache: `SAFE`, Exts: `IMPORTANT` |
| **Browsers** | Chrome, Edge, Brave, Firefox web/GPU caches (Profiles & logins protected) | `SAFE` |
| **AI / ML** | Hugging Face Hub models, Ollama LLMs, Claude Code, Claude Desktop, PyTorch weights | Weights: `IMPORTANT`, Cache: `SAFE` |

---

## 🖥️ User Interface Overview

PcClean features a dark-first developer dashboard aesthetic:

1. **Dashboard**: Ring/bar storage visualization for all connected drives, telemetry metric cards (Potential, Safe, Review, Protected, Large Files, Leftovers), and multi-drive grid.
2. **Storage Analyzer**: TreeSize/WizTree-style hierarchical tree with sorting by size, modified date, safety classification, search filters, and min-size filters.
3. **Cleanup Table**: Granular selection with developer presets (*Full Stack*, *Python/AI*, *Android*, *Safe Caches*), row-level inspect and clean buttons.
4. **Developer Tab**: Dedicated cards for Node/NVM, Python, Android, Flutter, Docker, VS Code, and AI models.
5. **Applications & Leftovers**: Installed Windows registry apps with official uninstaller launcher, plus residual AppData folder detection with confidence ratings (95%, 70%, 40%).
6. **Large File Finder**: Fast detection of massive videos, ISOs, virtual disks, archives, installers with category breakdown.
7. **Duplicate File Finder**: Two-stage detection (Stage 1: exact byte size grouping; Stage 2: streaming chunked SHA-256 hash validation).
8. **Protected Paths**: Add, view, and manage permanently shielded folders.
9. **History & Audit**: Detailed log of past deletions, reclaimed gigabytes, and skipped files.
10. **Details Inspector Panel**: Collapsible side drawer with exact monospace path, size, file counts, and deterministic rule-based impact explanations.
11. **Terminal Command Panel**: Real-time log output, progress monitoring, copyable logs, and report export.

---

## ⌨️ Command Line Interface (CLI)

PcClean shares the exact same core service and safety layer between the GUI and CLI:

```bash
# Scan active drive or specific drive
python -m pcclean scan C:
python -m pcclean scan --drive D:

# Preview cleanup candidates (Dry run - zero deletions)
python -m pcclean cleanup --preview

# Run safe cleanup (Prompted confirmation before moving to Recycle Bin)
python -m pcclean cleanup --safe

# Search for large files
python -m pcclean large-files C: --min-size 500MB
python -m pcclean large-files C: --min-size 1GB

# Manage protected paths
python -m pcclean protected list
python -m pcclean protected add "C:\MyValuableProject"
python -m pcclean protected remove "C:\MyValuableProject"

# Export system audit report (HTML, JSON, CSV, or TXT)
python -m pcclean report --output audit_report.html
python -m pcclean report --output audit_report.json
```

---

## 🧪 Testing

PcClean includes an extensive test suite verifying the Safety Engine, Protection Service, Quarantine, Storage Scanner, Leftovers Detector, and Duplicate Finder:

```bash
# Run all tests
python -m pytest tests/ -v
```

All destructive operations in tests are executed inside isolated temporary sandboxes and mock filesystem fixtures—**never** against production system roots.

---

## 📦 Building & Packaging Standalone Executables

### Prerequisites
- Python 3.11+
- Windows 10/11 x64

### 1. Build via PyInstaller

Run the PowerShell build script:
```powershell
.\build.ps1
```
Or with Batch:
```cmd
build.bat
```

For a single standalone EXE:
```powershell
.\build.ps1 -OneFile
```

The resulting executable will be in `dist\PcClean\PcClean.exe` (or `dist\PcClean.exe`).

### 2. Create Installer (`PcClean-Setup.exe`)
Compile `installer.iss` using Inno Setup 6:
```cmd
iscc installer.iss
```
This produces `dist\PcClean-Setup.exe` installing cleanly into `Program Files\PcClean` with Start Menu and Desktop shortcuts and clean uninstallation.

---

## 📄 License
MIT License. Copyright (c) 2026 PcClean Project.
