# PcClean Architecture & System Design

PcClean is designed as a developer-focused storage analyzer, cache cleaner, and disk maintenance utility for Windows. Unlike generic temp cleaners, PcClean is built from the ground up on the principle:

> **Show First. Explain Second. Clean Last.**

---

## High-Level System Architecture

PcClean is structured into clear architectural tiers to ensure separation of concerns, testability, and deterministic safety enforcement:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER                               │
│  ┌───────────────────────────────┐     ┌─────────────────────────────────┐  │
│  │     PySide6 Desktop GUI       │     │     Command Line Interface      │  │
│  │   (MainWindow, Views, Views)  │     │      (pcclean/cli.py)          │  │
│  └───────────────┬───────────────┘     └────────────────┬────────────────┘  │
└──────────────────┼──────────────────────────────────────┼───────────────────┘
                   │                                      │
                   ▼                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SERVICES LAYER                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌───────────┐  │
│  │ Storage & Drive Scanners │  │ Developer Tool Scanners  │  │ Duplicate │  │
│  │ (DriveService, Scanner)  │  │ (Node, Python, AI, SDK)  │  │ & Large   │  │
│  └──────────────┬───────────┘  └────────────┬─────────────┘  └─────┬─────┘  │
│                 │                           │                      │        │
│                 └─────────────────────┐     │     ┌────────────────┘        │
│                                       ▼     ▼     ▼                         │
│                                ┌──────────────────────┐                     │
│                                │    CleanupService    │                     │
│                                └──────────┬───────────┘                     │
└───────────────────────────────────────────┼─────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SAFETY & PROTECTION LAYER                           │
│  ┌─────────────────────────────┐           ┌─────────────────────────────┐  │
│  │        SafetyEngine         │           │      ProtectionService      │  │
│  │ (Path, Extension & Risk)    │◄─────────►│  (SQLite Protected Paths)   │  │
│  └──────────────┬──────────────┘           └─────────────────────────────┘  │
└─────────────────┼───────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION & STORAGE LAYER                          │
│  ┌─────────────────────────────┐           ┌─────────────────────────────┐  │
│  │     RecycleBinService       │           │      QuarantineService      │  │
│  │     (send2trash / Shell)    │           │ (Safe Staging + DB Catalog) │  │
│  └──────────────┬──────────────┘           └──────────────┬──────────────┘  │
│                 │                                         │                 │
│                 ▼                                         ▼                 │
│  ┌─────────────────────────────┐           ┌─────────────────────────────┐  │
│  │      Windows Filesystem     │           │    SQLite Local Database    │  │
│  │    (NTFS / ReFS Volumes)    │           │ (%LOCALAPPDATA%\PcClean)   │  │
│  └─────────────────────────────┘           └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Presentation Layer
- **Desktop UI (`ui/`):** Built with PySide6 (Qt for Python). Adopts a dark-first developer theme (`THEME_COLORS["dark"]`) with navigation sidebar, live telemetry dashboard, TreeSize-like storage tree, clean-up preview dialogs, and progress dialogs.
- **CLI (`pcclean/`):** Command-line tool with subcommands for headless CI/CD, automation, or remote administration:
  - `pcclean scan C:`
  - `pcclean clean --category npm --dry-run`
  - `pcclean protected list`
  - `pcclean report --output report.html`

### 2. Services Layer
The services layer consists of modular scanner and maintenance services:
- **`DriveService`:** Discovers fixed drives (SSD vs HDD detection via PowerShell/WMI fallback), optical drives, and volume labels.
- **`StorageScanner`:** Implements fast hierarchical directory traversal. Uses shallow inspections at maximum depths to eliminate filesystem hangs on large trees.
- **`DeveloperService` & Subsystem Scanners:**
  - `NodeService`: npm cache, pnpm store, yarn cache, Bun cache, nvm versions.
  - `PythonService`: pip cache, uv cache, poetry cache, virtual environments.
  - `AndroidService`: Android SDK platforms, build-tools, system images.
  - `FlutterService`: Flutter engine artifacts and pub cache.
  - `DockerService`: Named pipe liveness check (`is_process_running`) to avoid hanging when Docker Desktop is closed; retrieves dangling images, container leftovers, and build cache.
  - `AIService`: Model weights and caches for Hugging Face Hub, Ollama, PyTorch, Claude Code, and Codex.
  - `VSCodeService`: Extensions directory, cache storage, GPU cache.
  - `BrowserService`: Google Chrome, Edge, and Firefox caches.
- **`UninstallDetector`:** Scans `%APPDATA%`, `%LOCALAPPDATA%`, and `ProgramData` for folders whose parent applications are no longer registered in the Windows Uninstall Registry.
- **`DuplicateService`:** Memory-efficient duplicate file identification utilizing file size pre-grouping, 4KB partial hash comparison, and full SHA-256 verification.

### 3. Safety & Protection Layer
- **`SafetyEngine` (`services/safety_engine.py`):**
  - Evaluates candidate paths and returns a structured [`SafetyResult`](file:///E:/window-software/win-cleaner/models/safety_result.py).
  - Enforces absolute blocks on system roots (`C:\Windows`, `C:\Program Files`, `System Volume Information`).
  - Blocks deletion of sensitive developer assets (`.env`, `.ssh`, `.key`, `.pem`, `.gitconfig`, `.db`, `.sqlite`).
- **`ProtectionService` (`services/protection_service.py`):**
  - Manages user-configured protected directories stored in SQLite (`database/repositories.py`).
  - Guaranteed check: If path `P` is protected or a child of protected path `P_root`, any delete attempt is immediately rejected with `is_protected = True`.

### 4. Safe Execution Layer
- **`RecycleBinService`:** Dispatches deleted files to the native Windows Recycle Bin via `send2trash` or Windows Shell `SHFileOperationW`, preventing permanent data loss.
- **`QuarantineService`:** Moves files into `%LOCALAPPDATA%\PcClean\Quarantine\<timestamp>` with full path metadata recorded in SQLite, enabling instant one-click rollback/restore.
- **`CleanupService`:** Coordinates batch cleanup workflows, generating dry-run previews, enforcing pre-flight safety validations, and logging audit events to SQLite.

---

## Concurrency & Threading Model

To ensure a 60 FPS responsive UI and prevent freezes during I/O intensive disk walks:
1. **`WorkerThread` (`ui/scan_progress.py`):** Encapsulates long-running background tasks (scans, deletions, hashing) in dedicated Qt `QThread` instances.
2. **Signals & Slots:** Workers communicate with UI elements through thread-safe Qt signals:
   - `progress_signal = Signal(int, int, str)` (current, total, status description)
   - `finished_signal = Signal(object)` (result payload)
   - `error_signal = Signal(str)` (exception traceback)
3. **CancellationToken (`is_cancelled` callable):** Injected into all directory walks, hash calculations, and cleanup loops, enabling instant cancellation by the user at any point without resource leaks.
