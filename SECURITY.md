# Security Policy

The PcClean team takes the security and safety of user data with the utmost seriousness. PcClean is specifically engineered to protect developer environments, system configurations, source code, credentials, and databases from inadvertent deletion.

---

## 1. Supported Versions

We release security updates and critical patches for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0.0 | :x:                |

---

## 2. Reporting a Vulnerability

**DO NOT report potential security vulnerabilities or accidental data deletion bugs via public GitHub Issues or discussions.**

Instead, please report security vulnerabilities responsibly via private disclosure:

1. **Email:** Send details to `security@pcclean.dev`
2. **Subject:** `[SECURITY] Potential vulnerability in PcClean - <Brief Description>`
3. **Information to Include:**
   - Affected PcClean version and commit hash
   - Windows OS build and environment details
   - Step-by-step reproduction instructions
   - Proof of Concept (e.g., path structure demonstrating unintended evaluation)
   - Impact assessment (e.g., what files might be targeted or affected)

We will acknowledge receipt within **48 hours** and provide regular progress updates as we triage and prepare a fix.

---

## 3. Scope of Security Concerns

We consider the following to be high-severity security and safety defects:
- **Safety Bypass:** Any scenario where files matching protected extensions (`.env`, `.ssh`, `.key`, `.sqlite`, `.mdf`, etc.) or directories (`Windows`, `Program Files`, `.git`) are classified as deletable without warning.
- **Path Traversal / Reparse Point Loops:** Symlink, junction, or reparse point recursion resulting in deletion outside the scanned directory.
- **Privilege Escalation:** Unchecked parameter injection or execution of untrusted binaries during UAC elevation requests.
- **Credential Disclosure:** Writing tokens, environment variables, or private keys to log files or telemetry databases.

---

## 4. Security Principles Embedded in PcClean

PcClean's codebase incorporates defense-in-depth security measures:
1. **Multi-tier Safety Engine:** Every cleanup candidate is evaluated across path blacklists, filename blacklists, and extension blacklists before inclusion.
2. **Double Confirmation on Destructive Actions:** Dangerous or high-impact actions trigger modal warnings and explicit confirmation dialogs.
3. **Recycle Bin & Quarantine by Default:** Files are sent to the Windows Recycle Bin or PcClean Quarantine folder (`%LOCALAPPDATA%\PcClean\Quarantine`) whenever possible, preserving the ability to restore files.
4. **Elevation Isolation:** UAC elevation is requested only for specific system commands requiring Administrator privileges; standard scans execute under ordinary user permissions.
