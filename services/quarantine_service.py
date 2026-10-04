"""Quarantine Service: Move items safely to PcClean Quarantine with metadata for restoration."""

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from app.paths import get_quarantine_dir
from database.repositories import QuarantineRepository
from utils.filesystem import get_dir_size_and_count

logger = logging.getLogger("PcClean.QuarantineService")


class QuarantineService:
    def __init__(self, repo: QuarantineRepository | None = None):
        self.repo = repo or QuarantineRepository()
        self.quarantine_dir = get_quarantine_dir()

    def quarantine_item(self, path: Path, reason: str = "User Cleanup", category: str = "General") -> bool:
        """Move item to quarantine folder and record metadata."""
        if not path.exists():
            return False

        try:
            item_id = str(uuid.uuid4())[:8]
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_name = f"{timestamp_str}_{item_id}"
            dest_dir = self.quarantine_dir / folder_name
            dest_dir.mkdir(parents=True, exist_ok=True)

            target_dest = dest_dir / path.name

            # Calculate size before moving
            if path.is_file():
                size = path.stat().st_size
            else:
                size, _, _ = get_dir_size_and_count(path)

            # Move path
            shutil.move(str(path.resolve()), str(target_dest))

            # Write metadata file
            meta = {
                "original_path": str(path.resolve()),
                "quarantine_path": str(target_dest),
                "size_bytes": size,
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "category": category,
            }
            with open(dest_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            self.repo.add_item(
                original_path=meta["original_path"],
                quarantine_path=meta["quarantine_path"],
                size_bytes=size,
                reason=reason,
                category=category,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to quarantine {path}: {e}")
            return False

    def get_all(self) -> list[dict]:
        return self.repo.get_all()

    def restore_item(self, item_id: int) -> bool:
        """Restore quarantined item to its original location."""
        items = [i for i in self.repo.get_all() if i["id"] == item_id]
        if not items:
            return False
        item = items[0]
        q_path = Path(item["quarantine_path"])
        orig_path = Path(item["original_path"])

        if not q_path.exists():
            logger.error(f"Quarantined file not found at {q_path}")
            return False

        if orig_path.exists():
            logger.error(f"Cannot restore: destination {orig_path} already exists!")
            return False

        try:
            orig_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(q_path), str(orig_path))
            self.repo.mark_restored(item_id)
            # Remove container folder if empty
            parent = q_path.parent
            if parent.exists() and not list(parent.glob("*")):
                shutil.rmtree(parent, ignore_errors=True)
            return True
        except Exception as e:
            logger.error(f"Error restoring quarantine item {item_id}: {e}")
            return False

    def delete_permanently(self, item_id: int) -> bool:
        """Permanently delete a quarantined item from disk."""
        items = [i for i in self.repo.get_all() if i["id"] == item_id]
        if not items:
            return False
        item = items[0]
        q_path = Path(item["quarantine_path"])
        try:
            parent = q_path.parent
            if parent.exists():
                shutil.rmtree(parent, ignore_errors=True)
            self.repo.remove(item_id)
            return True
        except Exception as e:
            logger.error(f"Error permanently deleting quarantine item {item_id}: {e}")
            return False
