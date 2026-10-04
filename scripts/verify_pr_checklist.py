"""Verify Pull Request description checklist and safety requirements."""

import os
import sys


def verify_pr_body(body: str) -> list[str]:
    errors = []
    if not body or not body.strip():
        errors.append("PR description is completely empty. Please fill out the PR template.")
        return errors

    lines = body.splitlines()

    # 1. Check Safety & Destructive Operations Checklist
    in_safety_section = False
    safety_items_found = 0
    safety_unchecked = 0

    for line in lines:
        stripped = line.strip()
        if "Safety & Destructive Operations Checklist" in stripped:
            in_safety_section = True
            continue
        if in_safety_section and stripped.startswith("## "):
            in_safety_section = False

        if in_safety_section and (
            stripped.startswith("- [ ]") or stripped.startswith("- [x]") or stripped.startswith("- [X]")
        ):
            safety_items_found += 1
            if stripped.startswith("- [ ]"):
                safety_unchecked += 1
                errors.append(f"Unchecked safety item: {stripped[5:].strip()}")

    if safety_items_found == 0:
        errors.append("Safety Checklist section is missing from the PR description.")
    elif safety_unchecked > 0:
        errors.append(f"{safety_unchecked} safety checklist item(s) are still unchecked.")

    # 2. Check Type of Change (At least one must be checked)
    in_type_section = False
    type_checked = False

    for line in lines:
        stripped = line.strip()
        if "Type of Change" in stripped:
            in_type_section = True
            continue
        if in_type_section and stripped.startswith("## "):
            in_type_section = False

        if in_type_section and (stripped.startswith("- [x]") or stripped.startswith("- [X]")):
            type_checked = True

    if not type_checked:
        errors.append("Please select at least one checkbox under 'Type of Change'.")

    return errors


def main() -> int:
    pr_body = os.environ.get("PR_BODY", "")
    errors = verify_pr_body(pr_body)

    if errors:
        print("=" * 60)
        print("❌ Pull Request Checklist Validation FAILED:")
        print("=" * 60)
        for err in errors:
            print(f"  • {err}")
        print("\nPlease edit your PR description on GitHub and complete all required checklist items.")
        return 1

    print("=" * 60)
    print("✅ All Pull Request Checklist and Safety requirements are satisfied!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
