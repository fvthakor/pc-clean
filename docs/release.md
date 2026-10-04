# Packaging & Release Guide for PcClean

This document outlines the process for compiling, packaging, testing, and distributing PcClean releases.

---

## 1. Prerequisites for Building

1. **Python 3.11 / 3.12 (64-bit)**
2. **PyInstaller** (`pip install pyinstaller`)
3. **Inno Setup 6** (Optional, required for generating `PcClean-Setup.exe` installer)

---

## 2. Compiling the Standalone Executable (PyInstaller)

PcClean includes an optimized PyInstaller spec file: [`PcClean.spec`](file:///E:/window-software/win-cleaner/PcClean.spec).

To compile the standalone application:

```powershell
# Run the automated build script:
.\build.ps1

# Or run PyInstaller manually:
pyinstaller PcClean.spec --clean --noconfirm
```

The output will be produced in:
```
dist/
└── PcClean/
    ├── PcClean.exe        (Main binary)
    ├── resources/          (Icons, themes, QSS)
    ├── database/           (schema.sql)
    └── ...                 (Qt & Python DLLs)
```

### Verifying the Compiled Binary
Test launch the compiled binary:
```powershell
.\dist\PcClean\PcClean.exe
```
Confirm:
- Window loads without missing DLL or resource errors.
- Theme renders properly (dark theme styles applied).
- Scanning system drives executes without crashes.

---

## 3. Creating the Windows Installer (Inno Setup)

An Inno Setup script is provided at [`installer.iss`](file:///E:/window-software/win-cleaner/installer.iss).

If Inno Setup 6 is installed (`iscc.exe` in `PATH` or Program Files):
```powershell
& "C:\Program Files (x86)\Inno Setup 6\iscc.exe" installer.iss
```

This will produce:
```
dist/
└── PcClean-Setup-1.0.0.exe
```

Features included in the installer:
- Desktop shortcut (optional)
- Start Menu shortcuts
- Proper uninstaller registration in Windows Settings
- Clean uninstallation without orphaned files

---

## 4. Release Checklist

Before tagging and publishing a new release:

1. [ ] **Update Version:**
   - Update `version` in `pyproject.toml`.
   - Update `app_version` in `installer.iss`.
   - Update `CHANGELOG.md` with release notes and date.
2. [ ] **Run Lint & Tests:**
   ```powershell
   ruff check .
   ruff format --check .
   python -m pytest tests/ --cov
   ```
3. [ ] **Compile & Smoke Test Binary:**
   ```powershell
   .\build.ps1
   .\dist\PcClean\PcClean.exe
   ```
4. [ ] **Git Tagging:**
   ```powershell
   git commit -am "chore(release): bump version to 1.0.0"
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin main --tags
   ```
5. [ ] **GitHub Release:**
   - Publish GitHub Release targeting the `v1.0.0` tag.
   - Attach `PcClean-x64.zip` and `PcClean-Setup-1.0.0.exe`.
   - Paste release notes from `CHANGELOG.md`.
