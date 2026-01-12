# custom_dialogs.py - Özel Dialog Pencereleri
"""
MGD Task Scheduler Pro v4.0 - Custom Dialog System
Author: Mustafa GÜNEŞDOĞDU (MGdizayn)
Support: Ahmet KAHREMAN (CMX)

Standart tkinter messagebox yerine şık, modern CTkToplevel dialogs
"""

import customtkinter as ctk
from typing import Optional, Callable


class MGDDialog:
    """Base dialog sınıfı - Tüm özel dialoglar bundan türer."""
    
    def __init__(self, parent, title: str, message: str, dialog_type: str = "info"):
        self.parent = parent
        self.result = None
        
        # Dialog penceresi
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Pencereyi ortala
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (250 // 2)
        self.dialog.geometry(f"450x250+{x}+{y}")
        
        # Renk ve icon ayarla
        self.setup_style(dialog_type)
        
        # İçerik oluştur
        self.create_content(message)
        
    def setup_style(self, dialog_type: str):
        """Dialog tipine göre stil ayarla."""
        styles = {
            "info": {"icon": "ℹ️", "color": "#3b82f6", "bg": "#1e293b"},
            "success": {"icon": "✅", "color": "#22c55e", "bg": "#1e293b"},
            "warning": {"icon": "⚠️", "color": "#f59e0b", "bg": "#1e293b"},
            "error": {"icon": "❌", "color": "#ef4444", "bg": "#1e293b"},
            "question": {"icon": "❓", "color": "#8b5cf6", "bg": "#1e293b"}
        }
        
        self.style = styles.get(dialog_type, styles["info"])
        self.dialog.configure(fg_color=self.style["bg"])
    
    def create_content(self, message: str):
        """İçerik alanını oluştur."""
        # Icon frame
        icon_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        icon_frame.pack(pady=(30, 10))
        
        ctk.CTkLabel(
            icon_frame,
            text=self.style["icon"],
            font=("Arial", 48)
        ).pack()
        
        # Mesaj
        message_label = ctk.CTkLabel(
            self.dialog,
            text=message,
            font=("Segoe UI", 13),
            wraplength=380,
            justify="center"
        )
        message_label.pack(pady=20, padx=30)
        
        # Buton frame
        self.button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        self.button_frame.pack(pady=20)
    
    def show(self):
        """Dialogu göster ve sonucu bekle."""
        self.parent.wait_window(self.dialog)
        return self.result


class MGDInfoDialog(MGDDialog):
    """Bilgi mesajı dialogu."""
    
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent, title, message, "info")
        
        # Tamam butonu
        ctk.CTkButton(
            self.button_frame,
            text="Tamam",
            width=120,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=self.style["color"],
            command=self.on_ok
        ).pack()
    
    def on_ok(self):
        self.result = True
        self.dialog.destroy()


class MGDSuccessDialog(MGDDialog):
    """Başarı mesajı dialogu."""
    
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent, title, message, "success")
        
        ctk.CTkButton(
            self.button_frame,
            text="✓ Harika!",
            width=120,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=self.style["color"],
            command=self.on_ok
        ).pack()
    
    def on_ok(self):
        self.result = True
        self.dialog.destroy()


class MGDWarningDialog(MGDDialog):
    """Uyarı mesajı dialogu."""
    
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent, title, message, "warning")
        
        ctk.CTkButton(
            self.button_frame,
            text="Anladım",
            width=120,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=self.style["color"],
            command=self.on_ok
        ).pack()
    
    def on_ok(self):
        self.result = True
        self.dialog.destroy()


class MGDErrorDialog(MGDDialog):
    """Hata mesajı dialogu."""
    
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent, title, message, "error")
        
        ctk.CTkButton(
            self.button_frame,
            text="Kapat",
            width=120,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=self.style["color"],
            command=self.on_ok
        ).pack()
    
    def on_ok(self):
        self.result = True
        self.dialog.destroy()


class MGDQuestionDialog(MGDDialog):
    """Soru dialogu (Yes/No)."""
    
    def __init__(self, parent, title: str, message: str, yes_text: str = "Evet", no_text: str = "Hayır"):
        super().__init__(parent, title, message, "question")
        
        # Hayır butonu
        ctk.CTkButton(
            self.button_frame,
            text=no_text,
            width=120,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color="#64748b",
            hover_color="#475569",
            command=self.on_no
        ).pack(side="left", padx=10)
        
        # Evet butonu
        ctk.CTkButton(
            self.button_frame,
            text=yes_text,
            width=120,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=self.style["color"],
            hover_color="#7c3aed",
            command=self.on_yes
        ).pack(side="left", padx=10)
    
    def on_yes(self):
        self.result = True
        self.dialog.destroy()
    
    def on_no(self):
        self.result = False
        self.dialog.destroy()


class MGDInputDialog(MGDDialog):
    """Giriş dialogu (Text Input)."""
    
    def __init__(self, parent, title: str, message: str, placeholder: str = ""):
        super().__init__(parent, title, message, "question")
        
        # Input field
        self.entry = ctk.CTkEntry(
            self.dialog,
            width=350,
            height=40,
            placeholder_text=placeholder,
            font=("Segoe UI", 12)
        )
        self.entry.pack(pady=10)
        self.entry.focus_set()
        
        # Enter key binding
        self.entry.bind("<Return>", lambda e: self.on_ok())
        
        # Butonlar
        btn_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(
            btn_frame,
            text="İptal",
            width=100,
            height=35,
            font=("Segoe UI", 11, "bold"),
            fg_color="#64748b",
            command=self.on_cancel
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Tamam",
            width=100,
            height=35,
            font=("Segoe UI", 11, "bold"),
            fg_color=self.style["color"],
            command=self.on_ok
        ).pack(side="left", padx=10)
    
    def create_content(self, message: str):
        """Override - Input dialog için özel layout."""
        # Icon
        ctk.CTkLabel(
            self.dialog,
            text=self.style["icon"],
            font=("Arial", 36)
        ).pack(pady=(20, 5))
        
        # Mesaj
        ctk.CTkLabel(
            self.dialog,
            text=message,
            font=("Segoe UI", 12),
            wraplength=380,
            justify="center"
        ).pack(pady=5, padx=30)
    
    def on_ok(self):
        self.result = self.entry.get()
        self.dialog.destroy()
    
    def on_cancel(self):
        self.result = None
        self.dialog.destroy()


# Kolay kullanım için helper fonksiyonlar
def show_info(parent, title: str, message: str):
    """Bilgi dialogu göster."""
    return MGDInfoDialog(parent, title, message).show()


def show_success(parent, title: str, message: str):
    """Başarı dialogu göster."""
    return MGDSuccessDialog(parent, title, message).show()


def show_warning(parent, title: str, message: str):
    """Uyarı dialogu göster."""
    return MGDWarningDialog(parent, title, message).show()


def show_error(parent, title: str, message: str):
    """Hata dialogu göster."""
    return MGDErrorDialog(parent, title, message).show()


def ask_question(parent, title: str, message: str, yes_text: str = "Evet", no_text: str = "Hayır"):
    """Soru dialogu göster (True/False döner)."""
    return MGDQuestionDialog(parent, title, message, yes_text, no_text).show()


def ask_input(parent, title: str, message: str, placeholder: str = ""):
    """Giriş dialogu göster (string döner, iptal: None)."""
    return MGDInputDialog(parent, title, message, placeholder).show()
