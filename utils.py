# utils.py - Yardımcı Fonksiyonlar
"""
MGD Task Scheduler Pro v4.0 - Utility Functions
Author: Mustafa GÜNEŞDOĞDU (MGdizayn)
Support: Ahmet KAHREMAN (CMX)
"""

import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import subprocess

try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


class FileManager:
    """Dosya işlemleri yöneticisi."""
    
    @staticmethod
    def atomic_write(file_path: Path, data: Any, format: str = 'json'):
        """Atomic write ile güvenli yazma."""
        temp_path = file_path.with_suffix('.tmp')
        backup_path = file_path.with_suffix('.backup')
        
        try:
            if file_path.exists():
                shutil.copy2(file_path, backup_path)
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                if format == 'json':
                    json.dump(data, f, indent=4, ensure_ascii=False)
                else:
                    f.write(str(data))
            
            temp_path.replace(file_path)
            
            if backup_path.exists():
                backup_path.unlink()
            
            return True
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            
            if backup_path.exists():
                backup_path.replace(file_path)
            
            raise e
    
    @staticmethod
    def safe_read(file_path: Path, format: str = 'json', default: Any = None):
        """Güvenli okuma."""
        if not file_path.exists():
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if format == 'json':
                    return json.load(f)
                else:
                    return f.read()
        except Exception:
            backup_path = file_path.with_suffix('.backup')
            if backup_path.exists():
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        if format == 'json':
                            return json.load(f)
                        else:
                            return f.read()
                except:
                    pass
            return default
    
    @staticmethod
    def get_file_hash(file_path: Path) -> str:
        """Dosya hash'i hesapla."""
        if not file_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @staticmethod
    def cleanup_old_files(directory: Path, pattern: str, keep_count: int):
        """Eski dosyaları temizle."""
        try:
            files = sorted(directory.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
            for old_file in files[keep_count:]:
                old_file.unlink()
        except Exception as e:
            print(f"Cleanup error: {e}")


class NotificationManager:
    """Bildirim yöneticisi."""
    
    @staticmethod
    def send_desktop(title: str, message: str, app_name: str = "MGD Scheduler"):
        """Desktop bildirimi gönder."""
        if not PLYER_AVAILABLE:
            return False
        
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_name=app_name,
                timeout=10
            )
            return True
        except Exception:
            return False


class DateTimeHelper:
    """Tarih/saat yardımcı fonksiyonları."""
    
    @staticmethod
    def parse_datetime(date_str: str, format: str = "%d.%m.%Y %H:%M") -> Optional[datetime]:
        """Tarih string'ini parse et."""
        try:
            return datetime.strptime(date_str, format)
        except:
            return None
    
    @staticmethod
    def format_datetime(dt: datetime, format: str = "%d.%m.%Y %H:%M") -> str:
        """Datetime'ı string'e çevir."""
        return dt.strftime(format)
    
    @staticmethod
    def calculate_next_run(current: datetime, freq_type: str, freq_val: int) -> datetime:
        """Bir sonraki çalıştırma zamanını hesapla."""
        freq_val = max(1, freq_val)
        
        if freq_type == "Saatlik":
            return current + timedelta(hours=freq_val)
        elif freq_type == "Dakikalık":
            return current + timedelta(minutes=freq_val)
        elif freq_type == "Günlük":
            return current + timedelta(days=freq_val)
        elif freq_type == "Haftalık":
            return current + timedelta(weeks=freq_val)
        else:  # Günde X Kez
            hours_interval = 24 / freq_val
            return current + timedelta(hours=hours_interval)
    
    @staticmethod
    def humanize_duration(seconds: float) -> str:
        """Süreyi okunabilir formata çevir."""
        if seconds < 60:
            return f"{seconds:.1f} saniye"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} dakika"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} saat"
    
    @staticmethod
    def time_until(target: datetime) -> str:
        """Hedefe kalan süre."""
        now = datetime.now()
        if target < now:
            return "Geçti"
        
        delta = target - now
        
        if delta.days > 0:
            return f"{delta.days} gün {delta.seconds // 3600} saat"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600} saat {(delta.seconds % 3600) // 60} dakika"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60} dakika"
        else:
            return f"{delta.seconds} saniye"


class ProcessManager:
    """Process yönetimi."""
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """Process çalışıyor mu kontrol et."""
        try:
            if sys.platform == 'win32':
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                os.kill(pid, 0)
                return True
        except:
            return False
    
    @staticmethod
    def kill_process(pid: int) -> bool:
        """Process'i sonlandır."""
        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True)
            else:
                os.kill(pid, 9)
            return True
        except:
            return False


class SystemInfo:
    """Sistem bilgileri."""
    
    @staticmethod
    def get_platform_info() -> Dict[str, str]:
        """Platform bilgilerini al."""
        import platform
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
    
    @staticmethod
    def get_disk_usage(path: str = ".") -> Dict[str, int]:
        """Disk kullanımı."""
        try:
            total, used, free = shutil.disk_usage(path)
            return {
                'total': total,
                'used': used,
                'free': free,
                'percent': (used / total) * 100
            }
        except:
            return {}


def validate_email(email: str) -> bool:
    """Email validasyonu."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_file_size(size_bytes: int) -> str:
    """Dosya boyutunu okunabilir formata çevir."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """Dosya adını güvenli hale getir."""
    import re
    # Geçersiz karakterleri temizle
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Maksimum uzunluk kontrolü
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename


def get_template_path(template_name: str) -> Path:
    """Şablon dosya yolu."""
    return Path("templates") / f"{template_name}.json"


def load_template(template_name: str) -> Optional[Dict]:
    """Şablon yükle."""
    template_path = get_template_path(template_name)
    if template_path.exists():
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None


def save_template(template_name: str, task_data: Dict) -> bool:
    """Şablon kaydet."""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    template_path = get_template_path(template_name)
    try:
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False


def list_templates() -> List[str]:
    """Mevcut şablonları listele."""
    templates_dir = Path("templates")
    if not templates_dir.exists():
        return []
    
    return [f.stem for f in templates_dir.glob("*.json")]
