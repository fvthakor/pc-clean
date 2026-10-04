"""Database Repositories for PcClean."""

import logging
from datetime import datetime

from database.database import Database
from models.protected_path import ProtectedPath

logger = logging.getLogger("PcClean.Repositories")


class ProtectedPathRepository:
    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()

    def get_all(self) -> list[ProtectedPath]:
        results = []
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, path, name, reason, created_at, updated_at FROM protected_paths ORDER BY name ASC"
                )
                for row in cursor.fetchall():
                    results.append(
                        ProtectedPath(
                            id=row["id"],
                            path=row["path"],
                            name=row["name"],
                            reason=row["reason"],
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                    )
        except Exception as e:
            logger.error(f"Error fetching protected paths: {e}")
        return results

    def add(self, path: str, name: str, reason: str) -> bool:
        now = datetime.now().isoformat()
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO protected_paths (path, name, reason, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(path) DO UPDATE SET
                        name=excluded.name,
                        reason=excluded.reason,
                        updated_at=excluded.updated_at
                    """,
                    (path, name, reason, now, now),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding protected path {path}: {e}")
            return False

    def remove(self, path_or_id: str) -> bool:
        try:
            with self.db.get_connection() as conn:
                if str(path_or_id).isdigit():
                    conn.execute("DELETE FROM protected_paths WHERE id = ?", (int(path_or_id),))
                else:
                    conn.execute("DELETE FROM protected_paths WHERE path = ?", (str(path_or_id),))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing protected path {path_or_id}: {e}")
            return False

    def is_protected(self, path_str: str) -> bool:
        normalized = str(path_str).lower().rstrip("\\/")
        for item in self.get_all():
            item_norm = str(item.path).lower().rstrip("\\/")
            if normalized == item_norm or normalized.startswith(item_norm + "\\"):
                return True
        return False


class CleanupHistoryRepository:
    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()

    def add_entry(
        self,
        category: str,
        path: str,
        size_bytes: int,
        file_count: int,
        action: str,
        result: str,
        error_message: str | None = None,
    ) -> bool:
        now = datetime.now().isoformat()
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO cleanup_history (timestamp, category, path, size_bytes, file_count, action, result, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (now, category, path, size_bytes, file_count, action, result, error_message),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving cleanup history: {e}")
            return False

    def get_all(self, limit: int = 100) -> list[dict]:
        entries = []
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, timestamp, category, path, size_bytes, file_count, action, result, error_message FROM cleanup_history ORDER BY id DESC LIMIT ?",
                    (limit,),
                )
                for row in cursor.fetchall():
                    entries.append(dict(row))
        except Exception as e:
            logger.error(f"Error fetching cleanup history: {e}")
        return entries

    def clear(self) -> bool:
        try:
            with self.db.get_connection() as conn:
                conn.execute("DELETE FROM cleanup_history")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing cleanup history: {e}")
            return False


class QuarantineRepository:
    def __init__(self, db: Database | None = None):
        self.db = db or Database.get_instance()

    def add_item(
        self, original_path: str, quarantine_path: str, size_bytes: int, reason: str, category: str
    ) -> int | None:
        now = datetime.now().isoformat()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO quarantine_items (original_path, quarantine_path, size_bytes, timestamp, reason, category, is_restored)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                    """,
                    (original_path, quarantine_path, size_bytes, now, reason, category),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding quarantine item: {e}")
            return None

    def get_all(self) -> list[dict]:
        items = []
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, original_path, quarantine_path, size_bytes, timestamp, reason, category, is_restored FROM quarantine_items ORDER BY id DESC"
                )
                for row in cursor.fetchall():
                    items.append(dict(row))
        except Exception as e:
            logger.error(f"Error fetching quarantine items: {e}")
        return items

    def mark_restored(self, item_id: int) -> bool:
        try:
            with self.db.get_connection() as conn:
                conn.execute("UPDATE quarantine_items SET is_restored = 1 WHERE id = ?", (item_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking quarantine item restored: {e}")
            return False

    def remove(self, item_id: int) -> bool:
        try:
            with self.db.get_connection() as conn:
                conn.execute("DELETE FROM quarantine_items WHERE id = ?", (item_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing quarantine item: {e}")
            return False
