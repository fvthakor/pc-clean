"""SQLite Database Manager for PcClean."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from app.paths import get_database_path

logger = logging.getLogger("PcClean.Database")


class Database:
    _instance: Optional["Database"] = None

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or get_database_path()
        self._init_db()

    @classmethod
    def get_instance(cls, db_path: Path | None = None) -> "Database":
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            schema_file = Path(__file__).parent / "schema.sql"
            if schema_file.exists():
                with open(schema_file, encoding="utf-8") as f:
                    schema_sql = f.read()
                with self.get_connection() as conn:
                    conn.executescript(schema_sql)
                    conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
