# config.py - Yapılandırma Dosyası
"""
MGD Task Scheduler Pro v4.0 - Configuration Module
Author: Mustafa GÜNEŞDOĞDU (MGdizayn)
Support: Ahmet KAHREMAN (CMX)
"""

import json
import sys
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# 📂 SCRIPT DİZİNİ - Tüm dosyalar buradan çalışacak
SCRIPT_DIR = Path(__file__).parent.absolute()

@dataclass
class AppConfig:
    """Uygulama yapılandırma sınıfı."""
    
    # Genel Ayarlar
    app_name: str = "MGD Task Scheduler Pro"
    version: str = "4.0"
    language: str = "tr"
    
    # 📂 Dosya Yolları (Script dizinine göre)
    tasks_db: str = str(SCRIPT_DIR / "tasks.json")
    config_file: str = str(SCRIPT_DIR / "config.json")
    logs_dir: str = str(SCRIPT_DIR / "logs")
    backups_dir: str = str(SCRIPT_DIR / "backups")
    templates_dir: str = str(SCRIPT_DIR / "templates")
    history_dir: str = str(SCRIPT_DIR / "history")
    
    # Zamanlama Ayarları
    scheduler_interval: int = 15  # saniye
    max_task_timeout: int = 3600  # saniye (1 saat)
    retry_max: int = 3
    retry_delay: int = 60  # saniye
    
    # UI Ayarları
    theme: str = "dark"  # dark / light
    window_width: int = 1400
    window_height: int = 950
    sidebar_width: int = 380
    
    # Renk Temaları
    color_bg_dark: str = "#0f172a"
    color_bg_light: str = "#f8fafc"
    color_panel_dark: str = "#1e293b"
    color_panel_light: str = "#e2e8f0"
    color_text_dark: str = "#f8fafc"
    color_text_light: str = "#1e293b"
    color_accent: str = "#3b82f6"
    color_success: str = "#22c55e"
    color_danger: str = "#ef4444"
    color_warning: str = "#f59e0b"
    color_idle: str = "#64748b"
    color_paused: str = "#a855f7"
    
    # Telegram Ayarları
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_notify_on_start: bool = True
    telegram_notify_on_complete: bool = True
    telegram_notify_on_error: bool = True
    telegram_notify_on_retry: bool = False
    telegram_send_daily_report: bool = False
    telegram_daily_report_time: str = "23:00"
    
    # Bildirim Ayarları
    desktop_notifications_enabled: bool = True
    sound_enabled: bool = True
    
    # Backup Ayarları
    auto_backup: bool = True
    backup_keep_count: int = 10
    backup_on_exit: bool = True
    
    # Gelişmiş Ayarlar
    single_instance: bool = True
    start_minimized: bool = False
    minimize_to_tray: bool = True
    close_to_tray: bool = True
    log_level: str = "INFO"
    
    # Şifre Ayarları
    password_enabled: bool = False
    password_hash: str = ""  # SHA256 hash
    
    # Task History Ayarları
    keep_history_days: int = 30
    max_history_records: int = 1000
    
    def save(self, path: Optional[Path] = None):
        """Yapılandırmayı dosyaya kaydet."""
        if path is None:
            path = SCRIPT_DIR / "config.json"
        else:
            path = Path(path)
        
        try:
            print(f"📝 Config.save() başladı: {path}")
            
            # Dataclass'ı dict'e çevir
            config_dict = asdict(self)
            print(f"✅ asdict tamamlandı - {len(config_dict)} alan")
            
            # Telegram alanlarını kontrol et
            print(f"   telegram_enabled: {config_dict.get('telegram_enabled')}")
            print(f"   telegram_bot_token: {config_dict.get('telegram_bot_token', '')[:20]}..." if config_dict.get('telegram_bot_token') else "   telegram_bot_token: BOŞ")
            print(f"   telegram_chat_id: {config_dict.get('telegram_chat_id')}")
            print(f"   password_enabled: {config_dict.get('password_enabled')}")
            
            # JSON'a yaz
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Config dosyaya yazıldı: {path}")
            print(f"✅ Dosya boyutu: {path.stat().st_size} bytes")
            return True
        except Exception as e:
            print(f"❌ Config save error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @classmethod
    def load(cls, path: Optional[Path] = None):
        """Yapılandırmayı dosyadan yükle."""
        if path is None:
            path = SCRIPT_DIR / "config.json"
        else:
            path = Path(path)
        
        print(f"\n📖 Config.load() başladı: {path}")
        print(f"📂 Script dizini: {SCRIPT_DIR}")
        
        if path.exists():
            try:
                print(f"✅ Config dosyası bulundu")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"✅ JSON parse edildi - {len(data)} alan")
                print(f"   telegram_enabled: {data.get('telegram_enabled')}")
                print(f"   telegram_bot_token: {data.get('telegram_bot_token', '')[:20]}..." if data.get('telegram_bot_token') else "   telegram_bot_token: BOŞ")
                print(f"   telegram_chat_id: {data.get('telegram_chat_id')}")
                print(f"   password_enabled: {data.get('password_enabled')}")
                
                config = cls(**data)
                
                # 🔒 GÜVENLIK: Eğer şifre hash'i boşsa varsayılan oluştur
                if not config.password_hash:
                    import hashlib
                    config.password_hash = hashlib.sha256('1234'.encode()).hexdigest()
                    config.save(path)
                    print("🔒 Varsayılan şifre hash'i oluşturuldu (1234)")
                
                print(f"✅ Config yüklendi\n")
                return config
            except Exception as e:
                print(f"❌ Config load error: {e}")
                import traceback
                traceback.print_exc()
        
        # İlk kurulum - yeni config oluştur
        print("⚠️ Config dosyası bulunamadı - Yeni oluşturuluyor")
        config = cls()
        
        # 🔒 Varsayılan şifre hash'i ekle (1234)
        import hashlib
        config.password_hash = hashlib.sha256('1234'.encode()).hexdigest()
        
        config.save(path)
        print("🎉 İlk kurulum - Config oluşturuldu (Varsayılan şifre: 1234)\n")
        
        return config
    
    def get_colors(self):
        """Aktif temaya göre renkleri döndür."""
        if self.theme == "dark":
            return {
                'bg': self.color_bg_dark,
                'panel': self.color_panel_dark,
                'text': self.color_text_dark,
                'accent': self.color_accent,
                'success': self.color_success,
                'danger': self.color_danger,
                'warning': self.color_warning,
                'idle': self.color_idle,
                'paused': self.color_paused
            }
        else:
            return {
                'bg': self.color_bg_light,
                'panel': self.color_panel_light,
                'text': self.color_text_light,
                'accent': self.color_accent,
                'success': self.color_success,
                'danger': self.color_danger,
                'warning': self.color_warning,
                'idle': self.color_idle,
                'paused': self.color_paused
            }
    
    def validate_telegram(self):
        """Telegram ayarlarını doğrula."""
        if not self.telegram_enabled:
            return False
        return bool(self.telegram_bot_token and self.telegram_chat_id)


# Task kategorileri
TASK_CATEGORIES = [
    "Genel",
    "HBYS Entegrasyonu",
    "Veri İşleme",
    "Rapor Oluşturma",
    "DICOM İşlemleri",
    "Backup/Yedekleme",
    "Sistem Bakımı",
    "Bildirimler",
    "Test/Geliştirme"
]

# Task öncelik seviyeleri
TASK_PRIORITIES = {
    1: {"name": "Kritik", "color": "#dc2626", "emoji": "🔴"},
    2: {"name": "Yüksek", "color": "#f59e0b", "emoji": "🟡"},
    3: {"name": "Normal", "color": "#3b82f6", "emoji": "🔵"},
    4: {"name": "Düşük", "color": "#64748b", "emoji": "⚪"}
}

# Task durumları
TASK_STATUSES = {
    "idle": {"name": "Beklemede", "icon": "⏺", "color": "#64748b"},
    "running": {"name": "Çalışıyor", "icon": "▶", "color": "#22c55e"},
    "paused": {"name": "Duraklatıldı", "icon": "⏸", "color": "#a855f7"},
    "expired": {"name": "Süresi Doldu", "icon": "⏹", "color": "#78716c"},
    "failed": {"name": "Başarısız", "icon": "❌", "color": "#ef4444"},
    "success": {"name": "Başarılı", "icon": "✅", "color": "#22c55e"}
}

# Frekans tipleri
FREQUENCY_TYPES = [
    "Dakikalık",
    "Saatlik",
    "Günde X Kez",
    "Günlük",
    "Haftalık"
]
