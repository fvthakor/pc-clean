## Summary of Changes
<!-- Provide a clear, concise summary of the changes proposed in this PR. -->

## Motivation & Context
<!-- Why is this change necessary? Fixes # (issue number) -->

## Safety & Destructive Operations Checklist
<!-- MANDATORY: PcClean is built on the philosophy "Show First, Explain Second, Clean Last". -->
- [x] **No Unsafe Deletions:** I have verified that this change cannot delete `.env`, `.ssh`, `.git`, databases, system files, or user project code without explicit confirmation.
- [x] **SafetyEngine Integration:** Any new cleanup categories or file paths are routed through `SafetyEngine.evaluate_path()`.
- [x] **Recycle Bin / Quarantine Support:** Destructive operations default to Recycle Bin or quarantine, never permanent deletion without confirmation.
- [x] **Sandbox Testing:** Changes were tested in an isolated mock directory / sandbox, NEVER on live user project roots.

## Type of Change
- [x] 🐛 Bug fix (non-breaking change which fixes an issue)
- [x] ✨ New feature (non-breaking change adding functionality)
- [ ] 🛡️ Security / Safety hardening
- [ ] ⚡ Performance optimization
- [ ] 📝 Documentation update
- [ ] 🔧 Refactoring / Code quality

## Verification & Testing
<!-- Detail the test steps and paste verification outputs -->
- **Pytest Output:**
  ```powershell
  python -m pytest tests/
  ```
- **Ruff Lint & Format Output:**
  ```powershell
  ruff check .
  ruff format --check .
  ```
- **Platform Tested On:** Windows 10 / Windows 11 (specify build)

## Pre-Merge Checklist
- [x] My code adheres to the project's style guidelines.
- [x] I have added tests that prove my fix is effective or that my feature works.
- [x] All new and existing tests pass locally.
- [x] Documentation has been updated to reflect these changes if applicable.
