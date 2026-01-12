# telegram_manager.py - Telegram Bildirim Yöneticisi
"""
MGD Task Scheduler Pro v4.0 - Telegram Notification Manager
Author: Mustafa GÜNEŞDOĞDU (MGdizayn)
Support: Ahmet KAHREMAN (CMX)
"""

import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class TelegramManager:
    """Telegram bot yönetim sınıfı."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)
    
    def send_message(self, text: str, parse_mode: str = "HTML", disable_notification: bool = False) -> bool:
        """Telegram mesajı gönder."""
        if not self.enabled:
            return False
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram send error: {e}")
            return False
    
    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """Fotoğraf gönder."""
        if not self.enabled:
            return False
        
        url = f"{self.base_url}/sendPhoto"
        
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, files=files, data=data, timeout=30)
                return response.status_code == 200
        except Exception as e:
            print(f"Telegram photo send error: {e}")
            return False
    
    def send_document(self, document_path: str, caption: str = "") -> bool:
        """Doküman gönder."""
        if not self.enabled:
            return False
        
        url = f"{self.base_url}/sendDocument"
        
        try:
            with open(document_path, 'rb') as doc:
                files = {'document': doc}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, files=files, data=data, timeout=30)
                return response.status_code == 200
        except Exception as e:
            print(f"Telegram document send error: {e}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Bot bağlantısını test et."""
        if not self.bot_token:
            return {"success": False, "error": "Bot token boş"}
        
        url = f"{self.base_url}/getMe"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    return {
                        "success": True,
                        "bot_name": bot_info.get('first_name', 'Unknown'),
                        "bot_username": bot_info.get('username', 'Unknown')
                    }
            return {"success": False, "error": "Bot bulunamadı"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════════
    # ÖZEL BİLDİRİM MESAJLARI
    # ═══════════════════════════════════════════════════════════════════════
    
    def notify_task_started(self, task_name: str, priority: int = 3):
        """Görev başladı bildirimi."""
        emoji = {1: "🔴", 2: "🟡", 3: "🔵", 4: "⚪"}.get(priority, "🔵")
        
        message = (
            f"▶️ <b>GÖREV BAŞLADI</b>\n\n"
            f"{emoji} <b>{task_name}</b>\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        return self.send_message(message)
    
    def notify_task_completed(self, task_name: str, duration: float, success: bool = True):
        """Görev tamamlandı bildirimi."""
        icon = "✅" if success else "❌"
        status = "BAŞARILI" if success else "BAŞARISIZ"
        
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        duration_str = f"{minutes}dk {seconds}sn" if minutes > 0 else f"{seconds}sn"
        
        message = (
            f"{icon} <b>GÖREV {status}</b>\n\n"
            f"📌 <b>{task_name}</b>\n"
            f"⏱ Süre: {duration_str}\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        return self.send_message(message)
    
    def notify_task_error(self, task_name: str, error: str):
        """Görev hatası bildirimi."""
        message = (
            f"⚠️ <b>GÖREV HATASI</b>\n\n"
            f"📌 <b>{task_name}</b>\n"
            f"❌ Hata: <code>{error[:200]}</code>\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        return self.send_message(message)
    
    def notify_task_retry(self, task_name: str, current_retry: int, max_retry: int):
        """Görev tekrar denemesi bildirimi."""
        message = (
            f"🔄 <b>GÖREV TEKRAR DENENİYOR</b>\n\n"
            f"📌 <b>{task_name}</b>\n"
            f"🔢 Deneme: {current_retry}/{max_retry}\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        return self.send_message(message, disable_notification=True)
    
    def send_daily_report(self, stats: Dict[str, Any]):
        """Günlük rapor gönder."""
        message = (
            f"📊 <b>GÜNLÜK RAPOR</b>\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y')}\n\n"
            f"📈 <b>İstatistikler:</b>\n"
            f"▶️ Toplam Çalıştırma: {stats.get('total_runs', 0)}\n"
            f"✅ Başarılı: {stats.get('success', 0)}\n"
            f"❌ Başarısız: {stats.get('failed', 0)}\n"
            f"⏸ Duraklatıldı: {stats.get('paused', 0)}\n"
            f"⏹ Süresi Doldu: {stats.get('expired', 0)}\n\n"
            f"⏱ Toplam Çalışma Süresi: {stats.get('total_duration', '0')} saat"
        )
        return self.send_message(message)
    
    def send_system_info(self, info: Dict[str, Any]):
        """Sistem bilgisi gönder."""
        message = (
            f"💻 <b>SİSTEM BİLGİSİ</b>\n\n"
            f"🖥 Platform: {info.get('platform', 'N/A')}\n"
            f"🐍 Python: {info.get('python_version', 'N/A')}\n"
            f"💾 Disk Kullanımı: {info.get('disk_usage', 'N/A')}%\n"
            f"📝 Aktif Görev: {info.get('active_tasks', 0)}\n"
            f"⏰ Çalışma Süresi: {info.get('uptime', 'N/A')}"
        )
        return self.send_message(message)
    
    def send_welcome_message(self):
        """Hoş geldin mesajı."""
        message = (
            f"🚀 <b>MGD SCHEDULER BAŞLATILDI</b>\n\n"
            f"✅ Sistem aktif ve görevler izleniyor\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            f"🏥 <i>Hospital Automation Edition</i>\n"
            f"👨‍💻 Mustafa GÜNEŞDOĞDU (MGdizayn)"
        )
        return self.send_message(message)
    
    def send_shutdown_message(self, stats: Optional[Dict[str, Any]] = None):
        """Kapanış mesajı."""
        message = f"⏹ <b>MGD SCHEDULER KAPATILDI</b>\n\n"
        
        if stats:
            message += (
                f"📊 <b>Son Durum:</b>\n"
                f"▶️ Toplam Çalıştırma: {stats.get('total_runs', 0)}\n"
                f"✅ Başarılı: {stats.get('success', 0)}\n"
                f"❌ Başarısız: {stats.get('failed', 0)}\n\n"
            )
        
        message += f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        return self.send_message(message)


def create_telegram_manager(config) -> Optional[TelegramManager]:
    """Config'den Telegram manager oluştur."""
    if not config.telegram_enabled:
        return None
    
    if not config.telegram_bot_token or not config.telegram_chat_id:
        print("⚠️ Telegram ayarları eksik!")
        return None
    
    return TelegramManager(config.telegram_bot_token, config.telegram_chat_id)
