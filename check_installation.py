#!/usr/bin/env python3
# check_installation.py - Kurulum Kontrol Scripti
"""
MGD Task Scheduler Pro v4.0 - Installation Checker
Kurulumun doğru yapılıp yapılmadığını kontrol eder
"""

import sys
import os
from pathlib import Path

def check_installation():
    """Kurulum kontrolü yap."""
    print("=" * 70)
    print("MGD TASK SCHEDULER PRO v4.0 - KURULUM KONTROLÜ")
    print("=" * 70)
    print()
    
    script_dir = Path(__file__).parent.absolute()
    print(f"📂 Script Dizini: {script_dir}")
    print()
    
    # Gerekli dosyaları kontrol et
    required_files = [
        "main.py",
        "config.py",
        "telegram_manager.py",
        "utils.py",
        "task_history.py",
        "custom_dialogs.py",
        "requirements.txt"
    ]
    
    print("📋 Dosya Kontrolü:")
    print("-" * 70)
    
    all_ok = True
    for file_name in required_files:
        file_path = script_dir / file_name
        if file_path.exists():
            size = file_path.stat().st_size / 1024  # KB
            print(f"✅ {file_name:<25} ({size:.1f} KB)")
        else:
            print(f"❌ {file_name:<25} BULUNAMADI!")
            all_ok = False
    
    print()
    
    # Python versiyonu kontrol et
    print("🐍 Python Versiyonu:")
    print("-" * 70)
    py_version = sys.version_info
    print(f"   Version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    if py_version.major >= 3 and py_version.minor >= 8:
        print("   ✅ Python 3.8+ (Uygun)")
    else:
        print("   ❌ Python 3.8+ gerekli!")
        all_ok = False
    
    print()
    
    # Modül kontrolü
    print("📦 Modül Kontrolü:")
    print("-" * 70)
    
    modules = {
        "customtkinter": "customtkinter",
        "tkinterdnd2": "tkinterdnd2 (opsiyonel)",
        "pystray": "pystray",
        "PIL": "Pillow",
        "requests": "requests"
    }
    
    for module, name in modules.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            if "opsiyonel" in name:
                print(f"⚠️  {name} - Yüklenmemiş ama çalışır")
            else:
                print(f"❌ {name} - YÜKLENMELİ!")
                all_ok = False
    
    print()
    print("=" * 70)
    
    if all_ok:
        print("✅ KURULUM TAMAM - Program çalıştırılabilir!")
        print()
        print("Başlatmak için:")
        print(f"   cd {script_dir}")
        print(f"   python main.py")
    else:
        print("❌ KURULUM EKSIK - Yukarıdaki hataları düzeltin!")
        print()
        print("Eksik modülleri yüklemek için:")
        print(f"   cd {script_dir}")
        print(f"   pip install -r requirements.txt")
    
    print("=" * 70)
    print()
    
    return all_ok

if __name__ == "__main__":
    result = check_installation()
    sys.exit(0 if result else 1)
