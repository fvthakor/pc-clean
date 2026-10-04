-- PcClean Database Schema
CREATE TABLE IF NOT EXISTS protected_paths (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cleanup_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    category TEXT NOT NULL,
    path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    file_count INTEGER NOT NULL,
    action TEXT NOT NULL,
    result TEXT NOT NULL,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    drive_letter TEXT NOT NULL,
    total_space INTEGER NOT NULL,
    used_space INTEGER NOT NULL,
    potential_cleanup INTEGER NOT NULL,
    safe_cleanup INTEGER NOT NULL,
    duration_sec REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS quarantine_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT NOT NULL,
    quarantine_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    reason TEXT NOT NULL,
    category TEXT NOT NULL,
    is_restored INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_protected_paths_path ON protected_paths(path);
CREATE INDEX IF NOT EXISTS idx_cleanup_history_timestamp ON cleanup_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_quarantine_timestamp ON quarantine_items(timestamp);
