"""Constants and Enums for WinClean."""

from enum import StrEnum


class SafetyLevel(StrEnum):
    SAFE = "SAFE"
    SAFE_REDOWNLOAD = "SAFE_REDOWNLOAD"
    REVIEW = "REVIEW"
    IMPORTANT = "IMPORTANT"
    DANGEROUS = "DANGEROUS"
    BLOCKED = "BLOCKED"


class DriveType(StrEnum):
    FIXED_SSD = "SSD"
    FIXED_HDD = "HDD"
    FIXED_UNKNOWN = "Fixed"
    REMOVABLE = "USB / Removable"
    NETWORK = "Network"
    CDROM = "Optical"
    RAMDISK = "RAM Disk"
    UNKNOWN = "Unknown"


class ScanMode(StrEnum):
    FAST = "Fast Scan"
    DEEP = "Deep Scan"


class ActionType(StrEnum):
    SCAN = "Scan"
    CLEAN = "Clean"
    QUARANTINE = "Quarantine"
    RESTORE = "Restore"
    PROTECT = "Protect"
    UNPROTECT = "Unprotect"


class CleanupCategory(StrEnum):
    WINDOWS_TEMP = "Windows Temp"
    USER_TEMP = "User Temp"
    RECYCLE_BIN = "Recycle Bin"
    BROWSER_CACHE = "Browser Cache"
    NODE_CACHE = "Node.js & npm"
    PYTHON_CACHE = "Python & pip"
    ANDROID_SDK = "Android SDK"
    FLUTTER_CACHE = "Flutter & Pub"
    GRADLE_CACHE = "Gradle"
    DOCKER = "Docker"
    VSCODE = "VS Code"
    AI_MODELS = "AI / ML Models & Cache"
    APPLICATION_LEFTOVERS = "App Leftovers"
    LOGS_AND_CRASH = "Logs & Dumps"
    LARGE_FILES = "Large Files"
    DUPLICATES = "Duplicates"
    OTHER = "Other"


# File extensions that MUST NEVER be deleted by automated cleaners
PROTECTED_EXTENSIONS = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".ssh",
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".cer",
    ".crt",
    ".pub",
    ".id_rsa",
    ".id_ed25519",
    ".id_ecdsa",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".mdf",
    ".ldf",
    ".kdbx",
    ".gitconfig",
    ".bashrc",
    ".zshrc",
}

# Protected filename patterns (case-insensitive)
PROTECTED_FILENAMES = {
    "id_rsa",
    "id_rsa.pub",
    "id_ed25519",
    "id_ed25519.pub",
    "known_hosts",
    "authorized_keys",
    ".env",
    ".env.local",
    "credentials",
    "config.json",
    "settings.json",
    "private.key",
}

# System directory basenames that are strictly prohibited from deletion
SYSTEM_CRITICAL_DIRECTORIES = {
    "windows",
    "system32",
    "syswow64",
    "winsxs",
    "boot",
    "program files",
    "program files (x86)",
    "documents and settings",
    "system volume information",
    "$recycle.bin",
    "recovery",
}

# UI Theme Color Palettes (Dark-first Developer Palette)
THEME_COLORS = {
    "dark": {
        "bg_primary": "#0B0F14",
        "bg_secondary": "#111820",
        "bg_tertiary": "#17222E",
        "border": "#26313D",
        "border_light": "#364354",
        "text_primary": "#E6EDF3",
        "text_secondary": "#8B98A7",
        "text_muted": "#5B6876",
        "primary": "#4F8CFF",
        "primary_hover": "#659DFF",
        "success": "#36D399",
        "warning": "#F5B942",
        "danger": "#FF5C5C",
        "important": "#7C8CFF",
        "card_hover": "#16202B",
        "selection": "#1C2D42",
    },
    "light": {
        "bg_primary": "#F6F8FA",
        "bg_secondary": "#FFFFFF",
        "bg_tertiary": "#EAEEF2",
        "border": "#D0D7DE",
        "border_light": "#AFB8C1",
        "text_primary": "#1F2328",
        "text_secondary": "#656D76",
        "text_muted": "#8C959F",
        "primary": "#0969DA",
        "primary_hover": "#218BFF",
        "success": "#1A7F37",
        "warning": "#9A6700",
        "danger": "#CF222E",
        "important": "#8250DF",
        "card_hover": "#F3F4F6",
        "selection": "#DDF4FF",
    },
}
