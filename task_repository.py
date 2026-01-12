# task_repository.py - Görev Veri Yönetimi
"""
MGD Task Scheduler Pro v4.0 - Task Repository
Author: Mustafa GÜNEŞDOĞDU (MGdizayn)
Support: Ahmet KAHREMAN (CMX)
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any, Tuple
from utils import FileManager
from config import AppConfig

class TaskRepository:
    """Görevlerin veri erişim katmanı (Data Access Layer)."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.db_path = Path(config.tasks_db)
        self.backup_dir = Path(config.backups_dir)

        # Gerekli dizinleri oluştur
        self.backup_dir.mkdir(exist_ok=True, parents=True)

    def load_tasks(self) -> List[Dict[str, Any]]:
        """JSON dosyasından görevleri yükler ve varsayılan değerleri atar."""
        data = FileManager.safe_read(self.db_path, 'json', [])

        # Varsayılan alanları ekle (Data normalization)
        for task in data:
            task["status"] = "idle"
            task.setdefault("paused", False)
            task.setdefault("category", "Genel")
            task.setdefault("priority", 3)
            task.setdefault("run_count", 0)
            task.setdefault("success_count", 0)
            task.setdefault("fail_count", 0)
            task.setdefault("max_retries", self.config.retry_max)
            task.setdefault("retry_delay", self.config.retry_delay)
            task.setdefault("current_retry", 0)
            task.setdefault("last_error", "")
            task.setdefault("telegram_notify", True)

        return data

    def save_tasks(self, tasks: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Görev listesini diske kaydeder (Atomic write)."""
        try:
            FileManager.atomic_write(self.db_path, tasks, 'json')

            # Otomatik yedekleme
            if self.config.auto_backup:
                self.create_backup()
            return True, ""
        except Exception as e:
            return False, str(e)

    def create_backup(self) -> Tuple[bool, str]:
        """Mevcut veritabanının yedeğini alır."""
        backup_path = self.backup_dir / f"tasks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            if self.db_path.exists():
                shutil.copy2(self.db_path, backup_path)

                # Eski backup'ları temizle
                FileManager.cleanup_old_files(self.backup_dir, "tasks_backup_*.json", self.config.backup_keep_count)
                return True, ""
            return False, "Database file does not exist"
        except Exception as e:
            return False, str(e)

    def export_tasks_to_file(self, tasks: List[Dict[str, Any]], file_path: str) -> bool:
        """Görevleri belirtilen harici dosyaya aktarır."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Export Error: {e}")
            raise e

    def import_tasks_from_file(self, file_path: str, current_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Dosyadan görevleri okur ve mevcut listede olmayanları döndürür.
        Mevcut listeyi değiştirmez, sadece eklenecekleri döndürür.
        """
        new_tasks = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported = json.load(f)

            # Duplicate kontrolü (İsme göre)
            current_names = {t['name'] for t in current_tasks}

            for task in imported:
                if task['name'] not in current_names:
                    task['id'] = str(uuid4())  # Yeni ID ver
                    # Kritik alanları tamamla
                    task.setdefault("category", "Genel")
                    task.setdefault("priority", 3)
                    new_tasks.append(task)

            return new_tasks
        except Exception as e:
            print(f"Import Error: {e}")
            raise e
