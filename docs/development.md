# Developer Guide for PcClean

This guide covers setting up your local environment, coding standards, debugging, running tests, and working on PcClean.

---

## 1. Prerequisites

- **Windows 10 / 11 (64-bit)**
- **Python 3.11 or 3.12**
- **Git**

Verify Python version:
```powershell
python --version
# Output: Python 3.11.x or 3.12.x
```

---

## 2. Environment Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/fvthakor/pc-clean.git
   cd pc-clean
   ```

2. **Initialize a Virtual Environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Requirements:**
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Verify Installation:**
   ```powershell
   python -c "import PySide6, psutil, send2trash; print('All dependencies loaded successfully!')"
   ```

---

## 3. Running PcClean

### Launching the Desktop UI
```powershell
python main.py
```

### Launching the CLI
```powershell
# Display help
python -m pcclean --help

# Scan a drive
python -m pcclean scan C:

# Preview cleanup (dry run)
python -m pcclean clean --category npm --dry-run

# Manage protected paths
python -m pcclean protected list
python -m pcclean protected add "D:\ImportantProjects"
```

---

## 4. Code Quality & Formatting

We use **Ruff** for high-speed linting, import sorting, and code formatting:

```powershell
# Run lint checks
ruff check .

# Automatically apply lint fixes
ruff check --fix .

# Check formatting compliance
ruff format --check .

# Format all files
ruff format .
```

---

## 5. Running the Test Suite

Tests are organized into unit and integration suites under `tests/`:

```powershell
# Run all tests
python -m pytest tests/

# Run with coverage report
python -m pytest tests/ --cov=app --cov=services --cov=models --cov=utils --cov=winclean

# Run a specific test file
python -m pytest tests/unit/test_safety_engine.py -v
```

### Writing New Tests
- **Never touch live user directories!**
- Use the `temp_test_env` fixture (or `tmp_path`) defined in `tests/conftest.py`.
- Mock out system APIs such as `winreg` or subprocess calls where appropriate.

---

## 6. Directory Structure Overview

```
PcClean/
├── app/               # Configuration, constants, and path resolvers
├── database/          # SQLite connection and data repositories
├── models/            # Dataclasses (CleanCandidates, SafetyResult, DevTool, etc.)
├── services/          # Business logic and scanners (22 specialized services)
├── ui/                # PySide6 desktop interface and widgets
│   ├── dialogs/       # Modal preview and confirmation dialogs
│   ├── views/         # Specific view tabs (Dashboard, Storage, Dev, etc.)
│   └── main_window.py # Root application window
├── utils/             # Filesystem, hashing, formatting, Windows APIs
├── pcclean/          # CLI implementation and entrypoint
└── tests/             # Pytest test suite (unit + integration)
```
