import json
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime

class TaskRepository:
    """Handles data access for tasks (loading and saving to JSON)."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)

    def load_tasks(self, default_config=None):
        """Loads tasks from the JSON file."""
        if not self.db_path.exists():
            return []

        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

        # Data sanitization / Migration logic could go here
        # But for now, we follow the existing logic of ensuring defaults
        # However, to avoid circular dependency or passing big config objects,
        # we might just return raw data and let the Service/App layer handle validation
        # OR we pass the specific defaults we need.

        # In the original code, load_tasks added default values.
        # It's better to keep the Repository "dumb" (just I/O) or "smart" (valid objects).
        # Let's clean the data here to ensure consistency.

        if default_config:
            for task in data:
                self._apply_defaults(task, default_config)

        return data

    def save_tasks(self, tasks: list, backup_enabled: bool = False, backup_dir: Path = None, keep_backups: int = 10):
        """Saves tasks to the JSON file using atomic write."""
        temp_path = self.db_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)

            # Atomic move
            temp_path.replace(self.db_path)

            if backup_enabled and backup_dir:
                self.create_backup(backup_dir, keep_backups)

            return True
        except Exception as e:
            print(f"❌ Save error: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise e

    def _apply_defaults(self, task: dict, config):
        """Applies default values to a task object."""
        task["status"] = "idle"
        task.setdefault("paused", False)
        task.setdefault("category", "Genel")
        task.setdefault("priority", 3)
        task.setdefault("run_count", 0)
        task.setdefault("success_count", 0)
        task.setdefault("fail_count", 0)
        # Using config for these defaults
        task.setdefault("max_retries", getattr(config, 'retry_max', 3))
        task.setdefault("retry_delay", getattr(config, 'retry_delay', 60))

        task.setdefault("current_retry", 0)
        task.setdefault("last_error", "")
        task.setdefault("telegram_notify", True)

    def create_backup(self, backup_dir: Path, keep_count: int):
        """Creates a timestamped backup of the tasks file."""
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)

        backup_path = backup_dir / f"tasks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)

            # Cleanup old backups
            self._cleanup_old_backups(backup_dir, keep_count)
        except Exception as e:
            print(f"Backup error: {e}")

    def _cleanup_old_backups(self, backup_dir: Path, keep_count: int):
        """Removes old backup files."""
        try:
            files = sorted(backup_dir.glob("tasks_backup_*.json"), key=os.path.getmtime, reverse=True)
            for file in files[keep_count:]:
                file.unlink()
        except Exception:
            pass
