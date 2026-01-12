# main.py - MGD Task Scheduler Pro v4.0
"""
MGD Task Scheduler Pro v4.0 - Hospital Automation Edition
Author: Mustafa GÜNEŞDOĞDU (MGdizayn)
Support: Ahmet KAHREMAN (CMX)

Özellikler:
- Task Grupları/Kategoriler
- Telegram Bildirim Sistemi
- Task Öncelik Seviyeleri
- Detaylı Task History
- Settings Menüsü
- Dark/Light Theme Toggle
- Task Şablonları
- Toplu İşlemler
- Desktop Notifications
- Gelişmiş Rapor Sistemi
"""

import os
import sys
import socket
import json
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from tkinter import filedialog
import winreg

# CustomTkinter import
import customtkinter as ctk

# DND import
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    pass

# MGD Modules
from config import AppConfig, TASK_CATEGORIES, TASK_PRIORITIES, TASK_STATUSES, FREQUENCY_TYPES
from telegram_manager import TelegramManager, create_telegram_manager
from utils import (
    FileManager, NotificationManager, DateTimeHelper, 
    ProcessManager, SystemInfo, sanitize_filename,
    load_template, save_template, list_templates
)
from task_history import TaskHistoryManager, TaskHistoryRecord
from custom_dialogs import show_info, show_success, show_warning, show_error, ask_question, ask_input

# Tray icon
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LEVEL 1 KORUMA: WORKER MODE & SINGLE INSTANCE (ENHANCED SHIELD)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if os.environ.get("MGD_WORKER_MODE") == "true":
    # 🛡️ WORKER MODE - ENHANCED SHIELD
    # Alt süreç: Sadece kendisine verilen scripti çalıştır
    # Ana programı import etmesini engelle
    
    # SHIELD 1: PYTHONPATH temizle
    if "PYTHONPATH" in os.environ:
        del os.environ["PYTHONPATH"]
    
    # SHIELD 2: sys.path'ten current directory'yi kaldır
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != current_dir]
    
    # SHIELD 3: __main__ module'ü izole et
    if __name__ == "__main__":
        sys.modules.pop('__main__', None)
    
    if len(sys.argv) > 1:
        script_to_run = sys.argv[1]
        try:
            result = subprocess.run(
                [sys.executable, script_to_run],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                # Çevresel değişkenleri temizlenmiş haliyle geç
                env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"Worker Error: {e}", file=sys.stderr)
            sys.exit(1)
    sys.exit(0)
else:
    # Ana süreç: Single instance kontrolü
    class SingleInstance:
        def __init__(self):
            self.lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.port = 65432
            
        def is_running(self):
            try:
                self.lock_socket.bind(("127.0.0.1", self.port))
                return False
            except socket.error:
                return True
        
        def __del__(self):
            try:
                self.lock_socket.close()
            except:
                pass

    instance = SingleInstance()
    if instance.is_running():
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        show_warning(root, "MGD Scheduler", "⚠️ Program zaten çalışıyor!\n\nGörev çubuğunu veya sistem tepsisini kontrol edin.")
        root.destroy()
        sys.exit(0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANA UYGULAMA SINIFI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MGDSchedulerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Config yükle
        self.config = AppConfig.load()
        self.colors = self.config.get_colors()
        
        # 🔒 ŞİFRE KONTROLÜ
        if self.config.password_enabled:
            if not self.check_password():
                sys.exit(0)
        
        # DND kontrolü
        try:
            self.tk.call('package', 'require', 'tkdnd')
            self.dnd_available = True
        except Exception:
            self.dnd_available = False

        # Pencere ayarları
        self.title(f"{self.config.app_name} v{self.config.version}")
        self.geometry(f"{self.config.window_width}x{self.config.window_height}")
        ctk.set_appearance_mode(self.config.theme)
        self.configure(fg_color=self.colors['bg'])

        # Dizinleri oluştur
        for dir_name in [self.config.logs_dir, self.config.backups_dir, 
                         self.config.templates_dir, self.config.history_dir]:
            Path(dir_name).mkdir(exist_ok=True)

        # Veri yolları (cleanup'tan ÖNCE tanımlanmalı!)
        self.db_path = Path(self.config.tasks_db)
        self.backup_dir = Path(self.config.backups_dir)

        # Managers (cleanup'tan ÖNCE oluşturulmalı!)
        self.telegram = create_telegram_manager(self.config)
        self.history = TaskHistoryManager(self.config.history_dir)

        # 🧹 OTOMATIK TEMİZLİK - Her açılışta eski dosyaları temizle
        self.cleanup_old_files()

        # Uygulama durumu
        self.tasks = self.load_tasks()
        self.editing_task_id = None
        self.running = True
        self.is_tray_minimized = False
        self.start_time = datetime.now()

        # UI oluştur
        self.setup_ui()
        
        # Scheduler başlat
        self.monitor_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.monitor_thread.start()

        # Pencere kapatma eventi
        close_action = self.withdraw_to_tray if (TRAY_AVAILABLE and self.config.close_to_tray) else self.quit_app_final
        self.protocol('WM_DELETE_WINDOW', close_action)
        
        # 📱 AKILLI TELEGRAM BAŞLATMA
        self.after(1000, self.check_telegram_setup)
        
        print(f"✅ {self.config.app_name} v{self.config.version} başlatıldı")

    
    # ═══════════════════════════════════════════════════════════════════════════
    # TELEGRAM BAŞLATMA SİSTEMİ
    # ═══════════════════════════════════════════════════════════════════════════
    
    def check_telegram_setup(self):
        """Telegram ayarlarını kontrol et ve gerekirse kullanıcıyı yönlendir."""
        if self.telegram and self.config.validate_telegram():
            # ✅ Telegram aktif ve ayarlanmış - Hoş geldin mesajı gönder
            threading.Thread(target=self.telegram.send_welcome_message, daemon=True).start()
            print("📱 Telegram hoş geldin mesajı gönderildi")
        else:
            # ⚠️ Telegram ayarlanmamış - Kullanıcıyı bilgilendir
            response = ask_question(
                self,
                "📱 Telegram Bildirimleri",
                "Telegram bildirimleri aktif değil.\n\n"
                "Görev başlatma, tamamlanma ve hata bildirimlerini\n"
                "Telegram'dan almak ister misiniz?\n\n"
                "💡 Ücretsiz ve kurulumu 2 dakika!",
                yes_text="✅ Şimdi Ayarla",
                no_text="❌ Daha Sonra"
            )
            
            if response:
                # Kullanıcı ayarlamak istiyor - Ayarlar penceresini aç
                self.after(500, self.open_settings)
            else:
                # Daha sonra - Bilgilendirme yap
                print("ℹ️ Telegram bildirimleri kapalı. Ayarlardan aktif edebilirsiniz.")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # OTOMATIK TEMİZLİK SİSTEMİ
    # ═══════════════════════════════════════════════════════════════════════════
    
    def cleanup_old_files(self):
        """Eski log ve backup dosyalarını temizle."""
        try:
            # Log dosyalarını temizle (son 30 günü tut)
            log_dir = Path(self.config.logs_dir)
            if log_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=30)
                for log_file in log_dir.glob("*.log"):
                    try:
                        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            log_file.unlink()
                            print(f"🧹 Eski log silindi: {log_file.name}")
                    except:
                        pass
            
            # Backup dosyalarını temizle (config'deki sayıyı tut)
            FileManager.cleanup_old_files(
                self.backup_dir, 
                "tasks_backup_*.json", 
                self.config.backup_keep_count
            )
            
            # History dosyalarını temizle (son 30 günü tut)
            self.history.cleanup_old_records(self.config.keep_history_days)
            
            print("✅ Otomatik temizlik tamamlandı")
        except Exception as e:
            print(f"⚠️ Temizlik hatası: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ŞİFRE SİSTEMİ
    # ═══════════════════════════════════════════════════════════════════════════
    
    def check_password(self, title: str = "🔒 MGD Scheduler - Giriş", require_reason: bool = False):
        """Şifre kontrolü yap."""
        if not self.config.password_enabled:
            return True  # Şifre kapalıysa direkt geç
        
        import hashlib
        
        # Login penceresi
        login_window = ctk.CTkToplevel(self)
        login_window.title(title)
        login_window.geometry("400x300")
        login_window.resizable(False, False)
        login_window.transient(self)
        login_window.grab_set()
        
        # Pencereyi ortala
        login_window.update_idletasks()
        x = (login_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (login_window.winfo_screenheight() // 2) - (300 // 2)
        login_window.geometry(f"400x300+{x}+{y}")
        
        result = {"authenticated": False}
        
        frame = ctk.CTkFrame(login_window, fg_color=self.colors['panel'])
        frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Logo
        ctk.CTkLabel(frame, text="🔒", font=("Arial", 48)).pack(pady=(20, 10))
        
        if require_reason:
            ctk.CTkLabel(frame, text="GÜVENLIK KONTROLÜ", font=("Segoe UI", 14, "bold")).pack()
            ctk.CTkLabel(frame, text="Kritik işlem için şifre gerekli", font=("Segoe UI", 10), text_color=self.colors['idle']).pack(pady=(5, 15))
        else:
            ctk.CTkLabel(frame, text="MGD TASK SCHEDULER", font=("Segoe UI", 16, "bold")).pack()
            ctk.CTkLabel(frame, text="Lütfen şifrenizi girin", font=("Segoe UI", 10), text_color=self.colors['idle']).pack(pady=(5, 20))
        
        # Şifre girişi
        password_entry = ctk.CTkEntry(frame, width=300, height=40, show="●", placeholder_text="Şifre")
        password_entry.pack(pady=10)
        password_entry.focus_set()
        
        error_label = ctk.CTkLabel(frame, text="", font=("Segoe UI", 10), text_color=self.colors['danger'])
        error_label.pack()
        
        def validate_password():
            entered_password = password_entry.get()
            entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()
            
            if entered_hash == self.config.password_hash:
                result["authenticated"] = True
                login_window.destroy()
            else:
                error_label.configure(text="❌ Hatalı şifre!")
                password_entry.delete(0, "end")
                password_entry.focus_set()
        
        def on_enter(event):
            validate_password()
        
        password_entry.bind("<Return>", on_enter)
        
        # Giriş butonu
        ctk.CTkButton(
            frame, 
            text="🔓 GİRİŞ YAP", 
            width=300, 
            height=40, 
            font=("Segoe UI", 14, "bold"),
            fg_color=self.colors['success'],
            command=validate_password
        ).pack(pady=15)
        
        # Hint (sadece ilk girişte)
        if not require_reason:
            ctk.CTkLabel(frame, text="Varsayılan şifre: 1234", font=("Segoe UI", 8), text_color=self.colors['idle']).pack(pady=5)
        
        # Pencere kapatma
        def on_closing():
            result["authenticated"] = False
            login_window.destroy()
        
        login_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Bekle
        self.wait_window(login_window)
        
        return result["authenticated"]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # VERİ YÖNETİMİ
    # ═══════════════════════════════════════════════════════════════════════════
    
    def load_tasks(self):
        """JSON dosyasından görevleri yükle."""
        data = FileManager.safe_read(self.db_path, 'json', [])
        
        # Varsayılan alanları ekle
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
        
        print(f"📋 {len(data)} görev yüklendi")
        return data

    def save_tasks(self):
        """Güvenli kayıt."""
        try:
            FileManager.atomic_write(self.db_path, self.tasks, 'json')
            
            # Auto backup
            if self.config.auto_backup:
                self.create_backup()
        except Exception as e:
            print(f"❌ Kayıt hatası: {e}")
            self.log_to_report(f"!!! KAYIT HATASI: {e}")

    def create_backup(self):
        """Backup oluştur."""
        backup_path = self.backup_dir / f"tasks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # Eski backup'ları temizle
            FileManager.cleanup_old_files(self.backup_dir, "tasks_backup_*.json", self.config.backup_keep_count)
        except Exception as e:
            print(f"Backup error: {e}")

    def export_tasks(self):
        """Görevleri dışa aktar."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Tümü", "*.*")],
            initialfile=f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.tasks, f, indent=4, ensure_ascii=False)
                show_success(self, "Başarılı", "✅ Görevler dışa aktarıldı!")
                self.log_to_report(f"📤 Görevler dışa aktarıldı: {Path(file_path).name}")
            except Exception as e:
                show_error(self, "Hata", f"Dışa aktarma başarısız:\n{e}")

    def import_tasks(self):
        """Görevleri içe aktar."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("Tümü", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    imported = json.load(f)
                
                # Duplicate kontrolü
                new_tasks = []
                for task in imported:
                    if not any(t['name'] == task['name'] for t in self.tasks):
                        task['id'] = str(uuid4())  # Yeni ID ver
                        new_tasks.append(task)
                
                self.tasks.extend(new_tasks)
                self.save_tasks()
                self.refresh_task_list()
                show_success(self, "Başarılı", f"✅ {len(new_tasks)} görev içe aktarıldı!")
                self.log_to_report(f"📥 {len(new_tasks)} görev içe aktarıldı")
            except Exception as e:
                show_error(self, "Hata", f"İçe aktarma başarısız:\n{e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # VALİDASYON FONKSİYONLARI
    # ═══════════════════════════════════════════════════════════════════════════
    
    def validate_datetime_input(self, date_str, field_name="Tarih"):
        """Tarih formatını doğrula."""
        dt = DateTimeHelper.parse_datetime(date_str)
        if not dt:
            raise ValueError(
                f"❌ Geçersiz {field_name} formatı!\n\n"
                f"Beklenen: GG.AA.YYYY SS:DD\n"
                f"Örnek: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
        
        if field_name == "Başlangıç" and dt < datetime.now() - timedelta(minutes=5):
            if not messagebox.askyesno(
                "Geçmiş Tarih", 
                f"{field_name} geçmişte!\nYine de devam edilsin mi?"
            ):
                raise ValueError("Kullanıcı iptal etti")
        
        return dt

    def sanitize_path(self, path):
        """Dosya yolunu güvenli hale getir."""
        try:
            safe_path = Path(path).resolve()
            
            if ".." in str(safe_path):
                raise ValueError("Güvenli olmayan dosya yolu!")
            
            if not safe_path.exists():
                raise ValueError(f"Dosya bulunamadı:\n{safe_path}")
            
            valid_extensions = ['.exe', '.py', '.bat', '.cmd', '.ps1']
            if safe_path.suffix.lower() not in valid_extensions:
                if not messagebox.askyesno(
                    "Uyarı",
                    f"Bu dosya türü çalıştırılamayabilir: {safe_path.suffix}\n\nDevam edilsin mi?"
                ):
                    raise ValueError("Kullanıcı iptal etti")
            
            current_script = Path(__file__).resolve()
            if safe_path == current_script:
                raise ValueError("❌ Ana program kendisini çalıştıramaz!")
            
            return str(safe_path)
        except Exception as e:
            raise ValueError(f"Dosya yolu hatası:\n{e}")

    def check_duplicate_task(self, name, path, editing_id=None):
        """Duplicate görev kontrolü."""
        for task in self.tasks:
            if editing_id and task['id'] == editing_id:
                continue
            
            if task['name'].lower() == name.lower():
                return f"Bu isimde bir görev zaten var:\n{task['name']}"
            
            if Path(task['path']).resolve() == Path(path).resolve():
                return f"Bu dosya zaten görev listesinde:\n{task['name']}"
        
        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # UI OLUŞTURMA
    # ═══════════════════════════════════════════════════════════════════════════
    
    def setup_ui(self):
        """Ana UI yapısını oluştur."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sol sidebar ve sağ içerik
        self.create_sidebar()
        self.create_main_content()
        
        # Footer
        self.footer = ctk.CTkLabel(
            self, 
            text="MGD © 2025 | Kodlayan: Mustafa GÜNEŞDOĞDU (MGD) [MGdizayn] Bilgisayar Programcısı | Destek: Ahmet KAHREMAN (CMX) Birim Sorumlusu", 
            font=("Segoe UI", 10),
            text_color=self.colors['idle']
        )
        self.footer.grid(row=1, column=0, columnspan=2, pady=5)

        # DND kaydı (500ms sonra - widget'lar hazır olsun)
        self.after(500, self.register_dnd_manual)
        
        # Görevleri göster
        self.refresh_task_list()

    def create_sidebar(self):
        """Sol sidebar oluştur - Ultra kompakt."""
        self.sidebar = ctk.CTkFrame(self, width=self.config.sidebar_width, fg_color=self.colors['panel'], corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Logo/Başlık - Küçültüldü
        ctk.CTkLabel(
            self.sidebar, 
            text="⚡ MGD PLANLAYICI", 
            font=("Segoe UI", 16, "bold"), 
            text_color=self.colors['accent']
        ).pack(pady=(15, 2))
        
        ctk.CTkLabel(
            self.sidebar, 
            text="Hospital Automation", 
            font=("Segoe UI", 9, "italic"), 
            text_color=self.colors['idle']
        ).pack(pady=(0, 8))
        
        # Yeni görev butonu - Küçültüldü
        self.btn_reset_form = ctk.CTkButton(
            self.sidebar, 
            text="➕ YENİ GÖREV", 
            font=("Segoe UI", 12, "bold"), 
            fg_color="#0ea5e9", 
            hover_color="#0284c7", 
            height=32,
            command=self.clear_form
        )
        self.btn_reset_form.pack(pady=8, padx=25, fill="x")

        # Mod göstergesi - Küçültüldü
        self.lbl_mode = ctk.CTkLabel(
            self.sidebar, 
            text="📝 Yeni Kayıt", 
            font=("Segoe UI", 9, "italic"), 
            text_color=self.colors['idle']
        )
        self.lbl_mode.pack(pady=(0, 8))

        # Form alanları
        self.create_form_fields()
        
        # Ayarlar ve butonlar
        self.create_sidebar_buttons()

    def create_form_fields(self):
        """Form alanlarını oluştur - Ultra kompakt, boşluksuz."""
        # Görev adı
        ctk.CTkLabel(self.sidebar, text="📝 Görev Adı", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=25, pady=(2,1))
        self.entry_name = ctk.CTkEntry(self.sidebar, placeholder_text="HBYS Veri Aktarımı", width=320, height=28)
        self.entry_name.pack(pady=1)

        # Dosya yolu - Drag&Drop YOK, direkt gözat
        path_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        path_container.pack(pady=2, padx=25, fill="x")
        
        self.entry_path = ctk.CTkEntry(path_container, placeholder_text="📁 Dosya yolu", width=255, height=28)
        self.entry_path.pack(side="left")
        
        ctk.CTkButton(path_container, text="...", width=40, height=28, fg_color=self.colors['accent'], command=self.browse_file).pack(side="left", padx=(5,0))

        # Kategori & Öncelik - Yan yana
        cat_prior_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        cat_prior_frame.pack(pady=2, padx=25, fill="x")
        
        cat_container = ctk.CTkFrame(cat_prior_frame, fg_color="transparent")
        cat_container.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(cat_container, text="📁", font=("Segoe UI", 9)).pack(anchor="w")
        self.category = ctk.CTkOptionMenu(cat_container, values=TASK_CATEGORIES, width=155, fg_color=self.colors['bg'], height=28)
        self.category.pack()
        
        prior_container = ctk.CTkFrame(cat_prior_frame, fg_color="transparent")
        prior_container.pack(side="right", expand=True, fill="x")
        ctk.CTkLabel(prior_container, text="⚡", font=("Segoe UI", 9)).pack(anchor="w")
        self.priority = ctk.CTkOptionMenu(prior_container, values=["Kritik", "Yüksek", "Normal", "Düşük"], width=155, fg_color=self.colors['bg'], height=28)
        self.priority.set("Normal")
        self.priority.pack()

        # Separator mini
        ctk.CTkFrame(self.sidebar, height=1, fg_color=self.colors['idle']).pack(fill="x", padx=25, pady=5)

        # Tarih başlık
        ctk.CTkLabel(self.sidebar, text="⏰ Zamanlama", font=("Segoe UI", 9, "bold"), text_color=self.colors['accent']).pack(pady=2)
        
        # Başlangıç & Bitiş - Yan yana
        dates_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        dates_frame.pack(pady=1, padx=25, fill="x")
        
        start_container = ctk.CTkFrame(dates_frame, fg_color="transparent")
        start_container.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(start_container, text="Başlangıç", font=("Segoe UI", 8)).pack(anchor="w")
        self.entry_start = ctk.CTkEntry(start_container, width=155, height=28)
        self.entry_start.pack()
        self.entry_start.insert(0, datetime.now().strftime("%d.%m.%Y %H:%M"))
        
        end_container = ctk.CTkFrame(dates_frame, fg_color="transparent")
        end_container.pack(side="right", expand=True, fill="x")
        ctk.CTkLabel(end_container, text="Bitiş", font=("Segoe UI", 8)).pack(anchor="w")
        self.entry_end = ctk.CTkEntry(end_container, width=155, height=28)
        self.entry_end.pack()
        self.entry_end.insert(0, (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y %H:%M"))

        # Tekrar tipi & Frekans - Yan yana
        repeat_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        repeat_frame.pack(pady=2, padx=25, fill="x")
        
        type_container = ctk.CTkFrame(repeat_frame, fg_color="transparent")
        type_container.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(type_container, text="Tekrar", font=("Segoe UI", 8)).pack(anchor="w")
        self.period_type = ctk.CTkOptionMenu(type_container, values=FREQUENCY_TYPES, width=200, fg_color=self.colors['bg'], height=28)
        self.period_type.pack()
        
        freq_container = ctk.CTkFrame(repeat_frame, fg_color="transparent")
        freq_container.pack(side="right")
        ctk.CTkLabel(freq_container, text="Değer", font=("Segoe UI", 8)).pack(anchor="w")
        self.entry_freq = ctk.CTkEntry(freq_container, placeholder_text="2", width=95, height=28)
        self.entry_freq.pack()

        # Separator 2
        ctk.CTkFrame(self.sidebar, height=1, fg_color=self.colors['success']).pack(fill="x", padx=25, pady=8)

        # 🔥 ANA KAYDET BUTONU - BÜYÜK VE BELİRGİN
        self.btn_main_action = ctk.CTkButton(
            self.sidebar, 
            text="✅ KAYDET", 
            fg_color=self.colors['success'], 
            hover_color="#16a34a", 
            height=42, 
            font=("Segoe UI", 14, "bold"),
            command=self.handle_main_action,
            corner_radius=8
        )
        self.btn_main_action.pack(pady=8, padx=25, fill="x")

    def create_sidebar_buttons(self):
        """Sidebar alt butonları - Kompakt."""
        settings_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        settings_frame.pack(pady=5, fill="x", padx=25)
        
        self.switch_startup = ctk.CTkSwitch(settings_frame, text="🚀 Başlangıç", font=("Segoe UI", 9), command=self.toggle_startup)
        self.switch_startup.pack(pady=3)
        self.check_startup_status()

        # Butonlar - Kompakt
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.pack(pady=3, fill="x", padx=25)
        
        ctk.CTkButton(btn_frame, text="📥", width=70, height=28, fg_color="#4f46e5", command=self.import_tasks).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="📤", width=70, height=28, fg_color="#4f46e5", command=self.export_tasks).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="📊", width=70, height=28, fg_color="#4f46e5", command=self.show_statistics).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="⚙️", width=70, height=28, fg_color=self.colors['warning'], command=self.open_settings).pack(side="left", padx=2)

    def create_main_content(self):
        """Sağ ana içerik alanı."""
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_rowconfigure(1, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="📋 ZAMANLANMIŞ GÖREVLER", font=("Segoe UI", 24, "bold")).pack(side="left")
        
        self.lbl_stats = ctk.CTkLabel(header_frame, text="", font=("Segoe UI", 11), text_color=self.colors['idle'])
        self.lbl_stats.pack(side="left", padx=20)
        
        ctk.CTkButton(header_frame, text="📊 Raporu Dışa Aktar", width=150, fg_color="#4f46e5", command=self.export_report).pack(side="right")

        # Görev listesi
        self.task_list_frame = ctk.CTkScrollableFrame(
            self.main_content, 
            fg_color=self.colors['panel'], 
            label_text="Aktif Planlar",
            label_font=("Segoe UI", 14, "bold")
        )
        self.task_list_frame.grid(row=1, column=0, sticky="nsew")
        
        # Log alanı
        ctk.CTkLabel(self.main_content, text="📝 Çalışma Günlüğü", font=("Segoe UI", 12, "bold")).grid(row=2, column=0, sticky="w", pady=(20, 5))
        
        self.report_frame = ctk.CTkTextbox(
            self.main_content, 
            height=280, 
            fg_color="#020617", 
            text_color=self.colors['success'], 
            font=("Consolas", 11),
            wrap="word"
        )
        self.report_frame.grid(row=3, column=0, sticky="ew")

    
    # ═══════════════════════════════════════════════════════════════════════════
    # FORM İŞLEMLERİ
    # ═══════════════════════════════════════════════════════════════════════════
    
    def clear_form(self):
        """Formu temizle."""
        self.editing_task_id = None
        self.entry_name.delete(0, "end")
        self.entry_path.delete(0, "end")
        self.entry_freq.delete(0, "end")
        self.entry_start.delete(0, "end")
        self.entry_start.insert(0, datetime.now().strftime("%d.%m.%Y %H:%M"))
        self.entry_end.delete(0, "end")
        self.entry_end.insert(0, (datetime.now() + timedelta(days=365)).strftime("%d.%m.%Y %H:%M"))
        self.period_type.set("Saatlik")
        self.category.set("Genel")
        self.priority.set("Normal")
        
        self.lbl_mode.configure(text="📝 Yeni Kayıt", text_color=self.colors['idle'])
        self.btn_main_action.configure(text="✅ KAYDET", fg_color=self.colors['success'])
        self.entry_name.focus_set()

    def browse_file(self):
        """Dosya seç."""
        path = filedialog.askopenfilename(
            title="Çalıştırılacak Dosyayı Seç",
            filetypes=[("Çalıştırılabilir", "*.exe *.py *.bat *.cmd *.ps1"), ("Python", "*.py"), ("Tümü", "*.*")]
        )
        if path:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, str(Path(path).resolve()))
    
    def handle_drop(self, event):
        """Drag & drop handler."""
        path = event.data.strip('{}')
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, str(Path(path).resolve()))
    
    def register_dnd_manual(self):
        """DND kaydı - path entry için."""
        if not self.dnd_available:
            return
        try:
            # Path entry için DND kaydı
            self.entry_path.tk.call('tkdnd::drop_target', 'register', self.entry_path._w, 'DND_Files')
            self.entry_path.bind('<<Drop>>', self.handle_drop)
            print("✅ Drag & Drop kaydedildi")
        except Exception as e:
            print(f"⚠️ DND kayıt hatası: {e}")

    def handle_main_action(self):
        """Görev ekle/düzenle."""
        try:
            name = self.entry_name.get().strip()
            path = self.entry_path.get().strip()
            freq = self.entry_freq.get().strip()
            start_str = self.entry_start.get().strip()
            end_str = self.entry_end.get().strip()
            
            if not all([name, path, freq, start_str, end_str]):
                raise ValueError("❌ Tüm alanları doldurunuz!")
            
            safe_path = self.sanitize_path(path)
            freq_val = int(freq)
            if freq_val < 1:
                raise ValueError("❌ Frekans 1'den küçük olamaz!")
            
            start_dt = self.validate_datetime_input(start_str, "Başlangıç")
            end_dt = self.validate_datetime_input(end_str, "Bitiş")
            
            if end_dt <= start_dt:
                raise ValueError("❌ Bitiş zamanı, başlangıçtan sonra olmalı!")
            
            dup_error = self.check_duplicate_task(name, safe_path, self.editing_task_id)
            if dup_error:
                if not ask_question(self, "Benzer Görev", f"{dup_error}\n\nYine de eklensin mi?"):
                    return
            
            priority_map = {"Kritik": 1, "Yüksek": 2, "Normal": 3, "Düşük": 4}
            
            if self.editing_task_id:
                for task in self.tasks:
                    if task['id'] == self.editing_task_id:
                        task.update({
                            "name": name, "path": safe_path, "start": start_str, "end": end_str,
                            "freq_type": self.period_type.get(), "freq_val": freq_val, 
                            "next_run": start_str, "category": self.category.get(),
                            "priority": priority_map[self.priority.get()]
                        })
                        break
                self.log_to_report(f"✏️ Görev güncellendi: {name}")
            else:
                new_task = {
                    "id": str(uuid4()), "name": name, "path": safe_path, "start": start_str, "end": end_str,
                    "freq_type": self.period_type.get(), "freq_val": freq_val, "last_run": "Bekliyor",
                    "next_run": start_str, "status": "idle", "paused": False, "category": self.category.get(),
                    "priority": priority_map[self.priority.get()], "run_count": 0, "success_count": 0, 
                    "fail_count": 0, "max_retries": self.config.retry_max, "retry_delay": self.config.retry_delay,
                    "current_retry": 0, "last_error": "", "telegram_notify": True
                }
                self.tasks.append(new_task)
                self.log_to_report(f"➕ Yeni görev eklendi: {name}")
            
            self.save_tasks()
            self.clear_form()
            self.refresh_task_list()
            show_success(self, "Başarılı", "✅ Görev kaydedildi!")
            
        except ValueError as e:
            messagebox.showerror("Doğrulama Hatası", str(e))
        except Exception as e:
            show_error(self, "Hata", f"Beklenmeyen hata:\n{e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # GÖREV LİSTESİ YÖNETİMİ
    # ═══════════════════════════════════════════════════════════════════════════
    
    def refresh_task_list(self):
        """Görev listesini yenile."""
        if not self.running:
            return
        
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()
        
        self.update_statistics()
        
        if not self.tasks:
            no_task_label = ctk.CTkLabel(
                self.task_list_frame,
                text="📭 Henüz görev eklenmemiş\n\n👈 Sol panelden yeni görev oluşturabilirsiniz",
                font=("Segoe UI", 14),
                text_color=self.colors['idle']
            )
            no_task_label.pack(pady=100)
            return
        
        for task in self.tasks:
            self.create_task_card(task)

    def create_task_card(self, task):
        """Görev kartı oluştur."""
        card = ctk.CTkFrame(self.task_list_frame, fg_color=self.colors['bg'], corner_radius=10)
        card.pack(fill="x", padx=8, pady=6)
        
        # Sol: Durum ve öncelik
        left_frame = ctk.CTkFrame(card, fg_color="transparent", width=60)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        # Status
        status = task.get("status", "idle")
        paused = task.get("paused", False)
        
        if paused:
            status_info = {"icon": "⏸", "color": self.colors['paused']}
        elif status == "running":
            status_info = {"icon": "▶", "color": self.colors['success']}
        elif status == "expired":
            status_info = {"icon": "⏹", "color": TASK_STATUSES['expired']['color']}
        else:
            status_info = {"icon": "⏺", "color": self.colors['idle']}
        
        ctk.CTkLabel(left_frame, text=status_info['icon'], text_color=status_info['color'], font=("Arial", 28)).pack()
        
        # Öncelik
        priority = task.get('priority', 3)
        priority_emoji = TASK_PRIORITIES[priority]['emoji']
        ctk.CTkLabel(left_frame, text=priority_emoji, font=("Arial", 16)).pack()
        
        # Orta: Bilgiler
        mid_frame = ctk.CTkFrame(card, fg_color="transparent")
        mid_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # Görev adı ve kategori
        ctk.CTkLabel(mid_frame, text=f"📌 {task['name']} | 📁 {task.get('category', 'Genel')}", font=("Segoe UI", 14, "bold"), anchor="w").pack(fill="x")
        
        file_name = Path(task['path']).name
        ctk.CTkLabel(mid_frame, text=f"📄 {file_name}", font=("Segoe UI", 10), text_color=self.colors['idle'], anchor="w").pack(fill="x", pady=(2, 0))
        
        freq_text = f"{task['freq_val']} {task['freq_type'].lower()}"
        timing_text = f"⏰ Son: {task['last_run']} | Gelecek: {task['next_run']} | Tekrar: {freq_text}"
        ctk.CTkLabel(mid_frame, text=timing_text, font=("Segoe UI", 10), text_color=self.colors['idle'], anchor="w").pack(fill="x", pady=(2, 0))
        
        stats_text = f"📊 Çalıştırma: {task.get('run_count', 0)} | ✅ Başarılı: {task.get('success_count', 0)} | ❌ Başarısız: {task.get('fail_count', 0)}"
        ctk.CTkLabel(mid_frame, text=stats_text, font=("Segoe UI", 9), text_color=self.colors['accent'], anchor="w").pack(fill="x", pady=(2, 0))
        
        # Sağ: Butonlar
        btn_group = ctk.CTkFrame(card, fg_color="transparent")
        btn_group.pack(side="right", padx=10, pady=10)
        
        pause_text = "▶️ Devam" if paused else "⏸ Duraklat"
        pause_color = self.colors['success'] if paused else self.colors['warning']
        ctk.CTkButton(btn_group, text=pause_text, width=90, height=32, fg_color=pause_color, command=lambda t=task: self.toggle_pause(t)).pack(side="top", pady=2)
        
        ctk.CTkButton(btn_group, text="✏️ Düzenle", width=90, height=32, fg_color=self.colors['accent'], command=lambda t=task: self.load_task_to_edit(t)).pack(side="top", pady=2)
        
        ctk.CTkButton(btn_group, text="🗑️ Sil", width=90, height=32, fg_color=self.colors['danger'], command=lambda t=task: self.delete_task(t)).pack(side="top", pady=2)

    def update_statistics(self):
        """İstatistikleri güncelle."""
        total = len(self.tasks)
        active = sum(1 for t in self.tasks if not t.get('paused', False) and t.get('status') != 'expired')
        paused = sum(1 for t in self.tasks if t.get('paused', False))
        
        self.lbl_stats.configure(text=f"Toplam: {total} | Aktif: {active} | Duraklatıldı: {paused}")

    def toggle_pause(self, task):
        """Duraklat/devam."""
        task['paused'] = not task.get('paused', False)
        status = "Duraklatıldı" if task['paused'] else "Devam ettirildi"
        
        self.save_tasks()
        self.refresh_task_list()
        self.log_to_report(f"⏸ {task['name']} - {status}")

    def load_task_to_edit(self, task):
        """Düzenleme için yükle - Şifre korumalı."""
        # 🔒 Şifre kontrolü (eğer aktifse)
        if self.config.password_enabled:
            if not self.check_password("🔒 Güvenlik Kontrolü", require_reason=True):
                show_warning(self, "İptal", "⚠️ Şifre doğrulanamadı.\n\nGörev düzenlenemedi.")
                return
        
        self.editing_task_id = task['id']
        
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, task['name'])
        
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, task['path'])
        
        self.entry_start.delete(0, "end")
        self.entry_start.insert(0, task['start'])
        
        self.entry_end.delete(0, "end")
        self.entry_end.insert(0, task['end'])
        
        self.entry_freq.delete(0, "end")
        self.entry_freq.insert(0, str(task['freq_val']))
        
        self.period_type.set(task['freq_type'])
        self.category.set(task.get('category', 'Genel'))
        
        priority_names = {1: "Kritik", 2: "Yüksek", 3: "Normal", 4: "Düşük"}
        self.priority.set(priority_names.get(task.get('priority', 3), "Normal"))
        
        self.lbl_mode.configure(text=f"✏️ Düzenleme: {task['name'][:20]}...", text_color=self.colors['warning'])
        self.btn_main_action.configure(text="💾 GÜNCELLE", fg_color=self.colors['warning'])
        
        self.sidebar.focus_set()
        self.entry_name.focus_set()

    def delete_task(self, task):
        """Görevi sil - Şifre korumalı."""
        # 🔒 Şifre kontrolü (eğer aktifse)
        if self.config.password_enabled:
            if not self.check_password("🔒 Güvenlik Kontrolü", require_reason=True):
                show_warning(self, "İptal", "⚠️ Şifre doğrulanamadı.\n\nGörev silinemedi.")
                return
        
        if ask_question(self, "Görev Silme Onayı", f"❗ {task['name']}\n\nBu görev silinecek. Emin misiniz?"):
            self.tasks.remove(task)
            self.save_tasks()
            self.refresh_task_list()
            self.log_to_report(f"🗑️ Görev silindi: {task['name']}")

    # ═══════════════════════════════════════════════════════════════════════════
    # SCHEDULER LOOP
    # ═══════════════════════════════════════════════════════════════════════════
    
    def scheduler_loop(self):
        """Ana zamanlayıcı döngüsü."""
        print("🔄 Scheduler loop başlatıldı")
        
        while self.running:
            try:
                now = datetime.now()
                updated = False
                
                for task in self.tasks[:]:
                    try:
                        if task.get('paused', False):
                            continue
                        
                        next_run = datetime.strptime(task['next_run'], "%d.%m.%Y %H:%M")
                        end_time = datetime.strptime(task['end'], "%d.%m.%Y %H:%M")
                        
                        if now > end_time:
                            if task.get('status') != 'expired':
                                task['status'] = 'expired'
                                self.log_to_report(f"⏹ {task['name']} - Süre doldu")
                                updated = True
                            continue
                        
                        if now >= next_run:
                            threading.Thread(target=self.execute_task, args=(task,), daemon=True).start()
                            
                            new_time = DateTimeHelper.calculate_next_run(next_run, task['freq_type'], task['freq_val'])
                            
                            task['last_run'] = now.strftime("%d.%m.%Y %H:%M")
                            task['next_run'] = new_time.strftime("%d.%m.%Y %H:%M")
                            task['run_count'] = task.get('run_count', 0) + 1
                            updated = True
                    
                    except Exception as e:
                        self.log_to_report(f"!!! SCHEDULER HATA [{task.get('name', 'Bilinmeyen')}]: {e}")
                
                if updated and self.running:
                    self.save_tasks()
                    self.after(0, self.refresh_task_list)
            
            except Exception as e:
                print(f"Scheduler loop error: {e}")
            
            time.sleep(self.config.scheduler_interval)
        
        print("⏹ Scheduler loop sonlandırıldı")

    def execute_task(self, task):
        """Görevi çalıştır."""
        if not self.running:
            return
        
        task_name = task['name']
        path = Path(task['path'])
        
        current_script = Path(__file__).resolve()
        if path.resolve() == current_script:
            self.log_to_report(f"!!! ENGEL: Ana program kendisini çalıştıramaz [{task_name}]")
            return
        
        task['status'] = "running"
        self.after(0, self.refresh_task_list)
        
        start_time = time.time()
        success = False
        exit_code = -1
        error_msg = ""
        output_lines = []
        
        try:
            worker_env = os.environ.copy()
            worker_env["MGD_WORKER_MODE"] = "true"
            if "PYTHONPATH" in worker_env:
                del worker_env["PYTHONPATH"]
            
            if path.suffix.lower() == '.py':
                cmd = [sys.executable, str(path)]
                use_shell = False
            else:
                cmd = str(path)
                use_shell = True
            
            self.log_to_report(f"▶️ BAŞLATILDI: {task_name}")
            
            # Telegram bildirimi
            if self.telegram and task.get('telegram_notify', True) and self.config.telegram_notify_on_start:
                threading.Thread(target=self.telegram.notify_task_started, args=(task_name, task.get('priority', 3)), daemon=True).start()
            
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=use_shell,
                bufsize=1, encoding="utf-8", errors="replace", env=worker_env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            self.log_to_report(f"  └─ PID: {proc.pid}")
            
            try:
                for line in iter(proc.stdout.readline, ''):
                    if not self.running:
                        proc.kill()
                        break
                    if line.strip():
                        output_lines.append(line.strip())
                        self.log_to_report(f"  [{task_name}] {line.strip()}")
                
                proc.stdout.close()
                
                try:
                    exit_code = proc.wait(timeout=self.config.max_task_timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    error_msg = f"Timeout ({self.config.max_task_timeout}s)"
                    self.log_to_report(f"⚠️ TIMEOUT: {task_name} zorla sonlandırıldı")
                    task['fail_count'] = task.get('fail_count', 0) + 1
                    
                    if self.telegram and task.get('telegram_notify', True) and self.config.telegram_notify_on_error:
                        threading.Thread(target=self.telegram.notify_task_error, args=(task_name, error_msg), daemon=True).start()
                    return
                
                duration = time.time() - start_time
                
                if exit_code == 0:
                    success = True
                    self.log_to_report(f"✅ BAŞARILI: {task_name} ({duration:.1f}s)")
                    task['success_count'] = task.get('success_count', 0) + 1
                    task['current_retry'] = 0
                    
                    if self.telegram and task.get('telegram_notify', True) and self.config.telegram_notify_on_complete:
                        threading.Thread(target=self.telegram.notify_task_completed, args=(task_name, duration, True), daemon=True).start()
                else:
                    error_msg = f"Exit code: {exit_code}"
                    self.log_to_report(f"❌ HATA: {task_name} - {error_msg}")
                    task['fail_count'] = task.get('fail_count', 0) + 1
                    task['last_error'] = error_msg
                    
                    if self.telegram and task.get('telegram_notify', True) and self.config.telegram_notify_on_error:
                        threading.Thread(target=self.telegram.notify_task_error, args=(task_name, error_msg), daemon=True).start()
                    
                    self.handle_task_retry(task)
                
                # History kaydet
                record = TaskHistoryRecord(
                    id=str(uuid4()), task_id=task['id'], task_name=task_name,
                    start_time=datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
                    end_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    duration=duration, success=success, exit_code=exit_code,
                    error_message=error_msg, output="\n".join(output_lines[:50])
                )
                self.history.add_record(record)
            
            except Exception as e:
                error_msg = str(e)
                self.log_to_report(f"!!! ÇALIŞTIRMA HATASI [{task_name}]: {error_msg}")
                task['fail_count'] = task.get('fail_count', 0) + 1
                task['last_error'] = error_msg
                self.handle_task_retry(task)
        
        except Exception as e:
            error_msg = str(e)
            self.log_to_report(f"!!! BAŞLATMA HATASI [{task_name}]: {error_msg}")
            task['fail_count'] = task.get('fail_count', 0) + 1
            task['last_error'] = error_msg
        
        finally:
            task['status'] = "idle"
            if self.running:
                self.save_tasks()
                self.after(0, self.refresh_task_list)

    def handle_task_retry(self, task):
        """Retry mekanizması."""
        max_retries = task.get('max_retries', self.config.retry_max)
        current_retry = task.get('current_retry', 0)
        
        if current_retry < max_retries:
            task['current_retry'] = current_retry + 1
            retry_delay = task.get('retry_delay', self.config.retry_delay)
            
            self.log_to_report(f"🔄 TEKRAR: {task['name']} - {task['current_retry']}/{max_retries} ({retry_delay}s sonra)")
            
            next_retry = datetime.now() + timedelta(seconds=retry_delay)
            task['next_run'] = next_retry.strftime("%d.%m.%Y %H:%M")
            
            if self.telegram and task.get('telegram_notify', True) and self.config.telegram_notify_on_retry:
                threading.Thread(target=self.telegram.notify_task_retry, args=(task['name'], task['current_retry'], max_retries), daemon=True).start()
        else:
            self.log_to_report(f"⛔ MAX RETRY: {task['name']} - Maksimum deneme sayısına ulaşıldı")
            task['current_retry'] = 0

    # Diğer yardımcı fonksiyonlar
    def log_to_report(self, message):
        """Log yaz."""
        if not self.running:
            return
        
        def update():
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.report_frame.insert("end", f"[{timestamp}] {message}\n")
            self.report_frame.see("end")
        
        self.after(0, update)

    def export_report(self):
        """Log dışa aktar."""
        content = self.report_frame.get("1.0", "end").strip()
        if not content:
            show_success(self, "Bilgi", "Henüz log kaydı yok.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Text", "*.txt")],
            initialfile=f"mgd_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if file_path:
            try:
                import csv
                with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Zaman", "Mesaj"])
                    
                    for line in content.split('\n'):
                        if line.strip() and "]" in line:
                            parts = line.split("]", 1)
                            time_part = parts[0].replace("[", "").strip()
                            msg_part = parts[1].strip() if len(parts) > 1 else ""
                            writer.writerow([time_part, msg_part])
                
                show_success(self, "Başarılı", "Rapor dışa aktarıldı!")
            except Exception as e:
                show_error(self, "Hata", f"Rapor oluşturulamadı:\n{e}")

    def toggle_startup(self):
        """Windows başlangıç kaydı."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "MGD_Scheduler"
        exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if self.switch_startup.get():
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                self.log_to_report("🚀 Windows başlangıcı etkinleştirildi")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    self.log_to_report("🚫 Windows başlangıcı devre dışı bırakıldı")
                except FileNotFoundError:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            show_error(self, "Hata", f"Başlangıç ayarı değiştirilemedi:\n{e}")

    def check_startup_status(self):
        """Windows başlangıç durumunu kontrol et."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "MGD_Scheduler")
                self.switch_startup.select()
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except:
            pass

    def open_settings(self):
        """Ayarlar penceresi - Telegram & Şifre - Şifre korumalı."""
        # 🔒 Şifre kontrolü (eğer aktifse)
        if self.config.password_enabled:
            if not self.check_password("🔒 Güvenlik Kontrolü", require_reason=True):
                show_warning(self, "İptal", "⚠️ Şifre doğrulanamadı.\n\nAyarlara erişilemedi.")
                return
        
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("⚙️ Ayarlar")
        settings_window.geometry("600x500")
        settings_window.transient(self)
        settings_window.grab_set()
        
        # Telegram Ayarları
        telegram_frame = ctk.CTkFrame(settings_window, fg_color=self.colors['panel'])
        telegram_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(telegram_frame, text="📱 Telegram Ayarları", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Bot Token
        ctk.CTkLabel(telegram_frame, text="Bot Token:", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        token_entry = ctk.CTkEntry(telegram_frame, width=500, placeholder_text="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
        token_entry.pack(padx=20, pady=5)
        token_entry.insert(0, self.config.telegram_bot_token)
        
        # Chat ID
        ctk.CTkLabel(telegram_frame, text="Chat ID:", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        chat_entry = ctk.CTkEntry(telegram_frame, width=500, placeholder_text="123456789")
        chat_entry.pack(padx=20, pady=5)
        chat_entry.insert(0, self.config.telegram_chat_id)
        
        # Telegram aktif
        telegram_switch = ctk.CTkSwitch(telegram_frame, text="Telegram Bildirimlerini Aktif Et")
        telegram_switch.pack(pady=10)
        if self.config.telegram_enabled:
            telegram_switch.select()
        
        # Test butonu
        def test_telegram():
            self.config.telegram_bot_token = token_entry.get().strip()
            self.config.telegram_chat_id = chat_entry.get().strip()
            self.config.telegram_enabled = telegram_switch.get()
            
            test_mgr = TelegramManager(self.config.telegram_bot_token, self.config.telegram_chat_id)
            result = test_mgr.test_connection()
            
            if result.get('success'):
                # Bağlantı başarılı - Test mesajı gönder
                test_msg = (
                    f"✅ <b>TEST MESAJI</b>\n\n"
                    f"🤖 Bot: {result.get('bot_name')}\n"
                    f"👤 Kullanıcı: @{result.get('bot_username')}\n"
                    f"📱 Chat ID: {self.config.telegram_chat_id}\n\n"
                    f"🎉 MGD Scheduler başarıyla bağlandı!"
                )
                
                threading.Thread(
                    target=test_mgr.send_message,
                    args=(test_msg,),
                    daemon=True
                ).start()
                
                show_success(
                    self, 
                    "Başarılı", 
                    f"✅ Bağlantı başarılı!\n\n"
                    f"Bot: {result.get('bot_name')}\n"
                    f"Kullanıcı adı: @{result.get('bot_username')}\n\n"
                    f"📱 Test mesajı Telegram'a gönderildi!"
                )
            else:
                show_error(self, "Hata", f"❌ Bağlantı başarısız:\n{result.get('error')}")
        
        ctk.CTkButton(telegram_frame, text="🔍 Bağlantıyı Test Et", command=test_telegram).pack(pady=10)
        
        # Şifre Ayarları
        password_frame = ctk.CTkFrame(settings_window, fg_color=self.colors['panel'])
        password_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(password_frame, text="🔒 Şifre Ayarları", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Şifre aktif
        password_switch = ctk.CTkSwitch(password_frame, text="Program Açılışında Şifre İste")
        password_switch.pack(pady=5)
        if self.config.__dict__.get('password_enabled', False):
            password_switch.select()
        
        # Yeni şifre
        ctk.CTkLabel(password_frame, text="Yeni Şifre:", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        new_pass_entry = ctk.CTkEntry(password_frame, width=500, show="●", placeholder_text="Şifre belirleyin (boş bırakırsanız: 1234)")
        new_pass_entry.pack(padx=20, pady=5)
        
        # Kaydet butonu
        def save_settings():
            print("\n🔧 AYAR KAYDETME BAŞLADI")
            
            # Telegram ayarları
            self.config.telegram_bot_token = token_entry.get().strip()
            self.config.telegram_chat_id = chat_entry.get().strip()
            self.config.telegram_enabled = telegram_switch.get()
            
            print(f"📱 Telegram Token: {self.config.telegram_bot_token[:20]}..." if self.config.telegram_bot_token else "📱 Telegram Token: BOŞ")
            print(f"📱 Telegram Chat ID: {self.config.telegram_chat_id}")
            print(f"📱 Telegram Enabled: {self.config.telegram_enabled}")
            
            # Şifre ayarları - DATACLASS ATTRIBUTE OLARAK SET ET
            self.config.password_enabled = password_switch.get()
            new_password = new_pass_entry.get().strip()
            
            print(f"🔒 Password Enabled: {self.config.password_enabled}")
            print(f"🔒 New Password: {'***' if new_password else 'Girilmedi'}")
            
            if new_password:
                import hashlib
                self.config.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
                password_info = new_password
                print(f"🔒 Hash oluşturuldu: {self.config.password_hash[:20]}...")
            else:
                # Şifre değiştirilmemişse mevcut hash'i koru
                if not self.config.password_hash:
                    import hashlib
                    self.config.password_hash = hashlib.sha256('1234'.encode()).hexdigest()
                    print("🔒 Varsayılan hash (1234) oluşturuldu")
                password_info = "1234 (varsayılan)" if not new_password else "Mevcut şifre korundu"
            
            # 💾 KRİTİK: Config'i dosyaya kaydet
            print("💾 Config kaydediliyor...")
            save_success = self.config.save()
            print(f"💾 Kayıt sonucu: {'BAŞARILI ✅' if save_success else 'BAŞARISIZ ❌'}")
            
            if not save_success:
                show_error(self, "Hata", "❌ Ayarlar kaydedilemedi!\n\nconfig.json dosyasını kontrol edin.")
                return
            
            # 📱 Telegram manager'ı yeniden oluştur
            print("📱 Telegram manager yenileniyor...")
            old_telegram = self.telegram
            self.telegram = create_telegram_manager(self.config)
            print(f"📱 Telegram manager: {'Oluşturuldu ✅' if self.telegram else 'Oluşturulamadı ❌'}")
            
            # Telegram aktifse test mesajı gönder
            if self.telegram and self.config.telegram_enabled:
                print("📱 Telegram güncelleme mesajı gönderiliyor...")
                def send_update_msg():
                    self.telegram.send_message(
                        "⚙️ <b>AYARLAR GÜNCELLENDİ</b>\n\n"
                        f"✅ Telegram: {'Aktif' if self.config.telegram_enabled else 'Kapalı'}\n"
                        f"🔒 Şifre Koruması: {'Aktif' if self.config.password_enabled else 'Kapalı'}\n"
                        f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                    )
                threading.Thread(target=send_update_msg, daemon=True).start()
            
            # Başarı mesajı
            show_success(
                self, 
                "Başarılı", 
                f"✅ Ayarlar kaydedildi!\n\n"
                f"📱 Telegram: {'Aktif ✓' if self.config.telegram_enabled else 'Kapalı ✗'}\n"
                f"🔒 Şifre: {password_info}\n\n"
                f"💾 config.json güncellendi!"
            )
            
            print("✅ AYAR KAYDETME TAMAMLANDI\n")
            settings_window.destroy()
        
        ctk.CTkButton(settings_window, text="💾 KAYDET", height=40, font=("Segoe UI", 14, "bold"), fg_color=self.colors['success'], command=save_settings).pack(pady=20)
    
    def show_statistics(self):
        """İstatistikler penceresi."""
        stats = self.history.get_statistics(30)
        
        stats_window = ctk.CTkToplevel(self)
        stats_window.title("📊 İstatistikler (Son 30 Gün)")
        stats_window.geometry("700x600")
        stats_window.transient(self)
        
        frame = ctk.CTkScrollableFrame(stats_window, fg_color=self.colors['panel'])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Genel istatistikler
        ctk.CTkLabel(frame, text="📈 GENEL İSTATİSTİKLER", font=("Segoe UI", 18, "bold")).pack(pady=10)
        
        general_text = f"""
Toplam Çalıştırma: {stats['total_runs']}
✅ Başarılı: {stats['success']} ({stats['success_rate']:.1f}%)
❌ Başarısız: {stats['failed']}
⏱ Ortalama Süre: {stats['avg_duration']:.1f} saniye
⏱ Toplam Süre: {stats['total_duration']:.1f} saniye ({stats['total_duration']/3600:.1f} saat)
        """
        
        ctk.CTkLabel(frame, text=general_text, font=("Consolas", 12), justify="left").pack(pady=10)
        
        # Görev bazında
        if stats.get('task_stats'):
            ctk.CTkLabel(frame, text="📋 GÖREV BAZINDA İSTATİSTİKLER", font=("Segoe UI", 16, "bold")).pack(pady=(20,10))
            
            for task_id, data in stats['task_stats'].items():
                success_rate = (data['success'] / data['total'] * 100) if data['total'] > 0 else 0
                avg_duration = data['total_duration'] / data['total'] if data['total'] > 0 else 0
                
                task_text = f"""
{data['name']}
├─ Toplam: {data['total']} | ✅ {data['success']} | ❌ {data['failed']}
├─ Başarı Oranı: {success_rate:.1f}%
└─ Ort. Süre: {avg_duration:.1f}s
                """
                
                task_frame = ctk.CTkFrame(frame, fg_color=self.colors['bg'])
                task_frame.pack(fill="x", pady=5, padx=10)
                ctk.CTkLabel(task_frame, text=task_text, font=("Consolas", 10), justify="left").pack(pady=5, padx=10)
        
        # Export butonu
        def export_stats():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text", "*.txt"), ("CSV", "*.csv")],
                initialfile=f"statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"MGD SCHEDULER - İSTATİSTİKLER\n")
                    f.write(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                    f.write("="*50 + "\n\n")
                    f.write(general_text)
                    f.write("\n" + "="*50 + "\n\n")
                    
                    if stats.get('task_stats'):
                        for task_id, data in stats['task_stats'].items():
                            f.write(f"\n{data['name']}\n")
                            f.write(f"  Toplam: {data['total']}\n")
                            f.write(f"  Başarılı: {data['success']}\n")
                            f.write(f"  Başarısız: {data['failed']}\n\n")
                
                show_success(self, "Başarılı", "İstatistikler dışa aktarıldı!")
        
        ctk.CTkButton(stats_window, text="📤 Dışa Aktar", command=export_stats).pack(pady=10)

    def withdraw_to_tray(self):
        """Sistem tepsisine küçült."""
        if not TRAY_AVAILABLE:
            self.quit_app_final()
            return
        
        self.withdraw()
        self.is_tray_minimized = True
        
        icon_image = Image.new('RGB', (64, 64), color=self.colors['accent'])
        draw = ImageDraw.Draw(icon_image)
        draw.rectangle([10, 10, 54, 54], fill=self.colors['panel'], outline='#ffffff', width=2)
        
        menu = pystray.Menu(
            pystray.MenuItem("🔓 Göster", self.restore_from_tray),
            pystray.MenuItem("❌ Çıkış", self.quit_app_trigger)
        )
        
        self.icon = pystray.Icon("MGD_Scheduler", icon_image, "MGD Planlayıcı", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def restore_from_tray(self):
        """Sistem tepsisinden geri getir."""
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.deiconify()
        self.is_tray_minimized = False

    def quit_app_trigger(self):
        """Çıkış tetikleyici."""
        self.after(0, self.quit_app_final)

    def quit_app_final(self):
        """Uygulamayı kapat."""
        print("🛑 Uygulama kapatılıyor...")
        
        self.running = False
        
        if hasattr(self, 'icon'):
            try:
                self.icon.stop()
            except:
                pass
        
        if self.config.backup_on_exit:
            self.create_backup()
        
        self.save_tasks()
        
        # Telegram bildirimi
        if self.telegram:
            stats = self.history.get_statistics(1)
            threading.Thread(target=self.telegram.send_shutdown_message, args=(stats,), daemon=True).start()
            time.sleep(0.5)  # Mesajın gönderilmesini bekle
        
        try:
            self.update_idletasks()
            self.quit()
            self.destroy()
        except:
            pass
        
        print("✅ Uygulama kapatıldı")
        sys.exit(0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ANA PROGRAM GİRİŞİ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    try:
        print("=" * 80)
        print("MGD TASK SCHEDULER PRO v4.0 - BAŞLATILIYOR")
        print("=" * 80)
        
        app = MGDSchedulerApp()
        app.mainloop()
        
    except KeyboardInterrupt:
        print("❌ Kullanıcı tarafından iptal edildi (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Kritik hata: {e}")
        show_error(self, "Kritik Hata", f"Program başlatılamadı:\n{e}")
        sys.exit(1)

