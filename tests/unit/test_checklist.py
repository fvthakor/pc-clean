"""Tests for PR checklist validator script."""

from scripts.verify_pr_checklist import verify_pr_body


def test_empty_pr_body():
    errors = verify_pr_body("")
    assert len(errors) > 0
    assert "completely empty" in errors[0]


def test_unchecked_safety_items():
    body = """
## Safety & Destructive Operations Checklist
- [ ] **No Unsafe Deletions:** I have verified...
- [x] **SafetyEngine Integration:** Any new cleanup...
- [ ] **Recycle Bin / Quarantine Support:** Destructive...
- [x] **Sandbox Testing:** Changes were tested...

## Type of Change
- [x] 🐛 Bug fix (non-breaking change which fixes an issue)
"""
    errors = verify_pr_body(body)
    assert len(errors) == 3
    assert any("No Unsafe Deletions" in e for e in errors)
    assert any("Recycle Bin" in e for e in errors)


def test_fully_checked_pr_body():
    body = """
## Summary of Changes
Fixed bugs and added project cleaner.

## Safety & Destructive Operations Checklist
- [x] **No Unsafe Deletions:** I have verified that this change cannot delete .env, .ssh, .git.
- [x] **SafetyEngine Integration:** Any new cleanup categories are routed through SafetyEngine.
- [x] **Recycle Bin / Quarantine Support:** Destructive operations default to Recycle Bin.
- [x] **Sandbox Testing:** Changes were tested in an isolated mock sandbox.

## Type of Change
- [x] 🐛 Bug fix (non-breaking change which fixes an issue)
- [x] ✨ New feature (non-breaking change adding functionality)

## Pre-Merge Checklist
- [x] My code adheres to the project's style guidelines.
"""
    errors = verify_pr_body(body)
    assert errors == []
