# Contributing to PcClean

Thank you for your interest in contributing to **PcClean**! We welcome bug fixes, documentation improvements, new developer ecosystem caches, and storage analysis enhancements.

PcClean is built with a primary commitment to **developer safety**:
> **Show First. Explain Second. Clean Last.**

Every contribution must preserve and reinforce this principle.

---

## 1. Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to security@pcclean.dev.

---

## 2. Getting Started

### Prerequisites
- **Operating System:** Windows 10 (version 1809+) or Windows 11 (x64)
- **Python:** Python 3.11 or 3.12 (64-bit)
- **Git**

### Local Development Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/fvthakor/pc-clean.git
   cd pc-clean
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Run the application:**
   - **GUI mode:**
     ```powershell
     python main.py
     ```
   - **CLI mode:**
     ```powershell
     python -m pcclean --help
     python -m pcclean scan C:
     ```

---

## 3. Development Guidelines & Workflow

### Branch Naming Conventions
- `feature/<short-description>`: New features, UI panels, cache scanners
- `fix/<short-description>`: Bug fixes and performance improvements
- `safety/<short-description>`: SafetyEngine updates and protection rules
- `docs/<short-description>`: Documentation additions and updates

### Commit Message Conventions
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat(scanner): add Bun cache detection`
- `fix(docker): handle daemon not running gracefully without timeout`
- `safety(engine): block deletion of .pem and .key files in all subdirectories`
- `docs(safety): document quarantined restore flow`
- `test(cleanup): add sandbox test for permission denied handling`

---

## 4. Safety Requirements for Code Changes

PcClean's number one feature is reliability and safety. If a PR risks unintended data loss, it will not be merged.

1. **Never Hardcode Direct Deletions:**
   All deletions MUST route through [`CleanupService`](file:///E:/window-software/win-cleaner/services/cleanup_service.py) and [`SafetyEngine`](file:///E:/window-software/win-cleaner/services/safety_engine.py).
2. **Default to Recycle Bin or Quarantine:**
   Permanent deletion (`os.remove`, `shutil.rmtree`) should only occur when Recycle Bin is disabled or explicitly overridden by user setting.
3. **Protected Extensions & Paths:**
   Never bypass blacklist checks for `.env`, `.git`, `.ssh`, `.sqlite`, `.pem`, etc.
4. **Isolated Test Sandboxes:**
   **NEVER write tests that scan or delete real user folders or system paths.** Always use `tempfile.mkdtemp` or pytest's `tmp_path` fixture.

---

## 5. Running Tests and Quality Checks

Before submitting a Pull Request, run the full verification pipeline locally:

```powershell
# 1. Run all unit and integration tests
python -m pytest tests/ --cov=app --cov=services --cov=models --cov=utils --cov=winclean

# 2. Check code style and linting
ruff check .

# 3. Check code formatting
ruff format --check .

# 4. Run static security audit
bandit -r app/ services/ utils/ pcclean/ -ll -x tests/
```

To auto-format your code with Ruff:
```powershell
ruff format .
ruff check --fix .
```

---

## 6. Submitting a Pull Request

1. Push your branch to your fork on GitHub.
2. Open a Pull Request targeting the `main` branch.
3. Complete all sections of the [Pull Request Template](.github/pull_request_template.md).
4. Ensure all CI checks (pytest, ruff lint, build) pass.
5. Address any review feedback from maintainers.
