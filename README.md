# 🚀 MGD Task Scheduler Pro v4.0
## Hospital Automation Edition - ULTRA COMPACT + SECURED

**Geliştirici:** Mustafa GÜNEŞDOĞDU (MGdizayn)  
**Destek:** Ahmet KAHREMAN (CMX)  
**Kurum:** Nazilli Devlet Hastanesi - IT Departmanı

---

## 📋 Özellikler

### ✨ Temel Özellikler
- ✅ **Zamanlanmış Görev Yönetimi** - Dakikalık, saatlik, günlük, haftalık periyodlar
- ✅ **Telegram Bot Entegrasyonu** - Anlık bildirimler ve raporlar
- ✅ **Task Kategorileri** - Görevleri gruplandırma
- ✅ **Öncelik Seviyeleri** - Kritik, Yüksek, Normal, Düşük
- ✅ **Detaylı İstatistikler** - Başarı oranları, çalışma süreleri
- ✅ **Task History** - Tüm görev çalıştırmalarının kaydı
- ✅ **Custom Modern Dialogs** - Şık, modern bildirim pencereleri
- ✅ **Şifre Koruması** - SHA256 şifreli güvenli giriş

### 🔒 Güvenlik Özellikleri
- ✅ **Single Instance** - Çift açılma koruması
- ✅ **Enhanced Worker Shield** - 3 katmanlı izolasyon sistemi
  - PYTHONPATH temizliği
  - sys.path izolasyonu
  - __main__ module koruması
- ✅ **Atomic File Operations** - Veri bozulması koruması
- ✅ **Auto Cleanup System** - Otomatik log/backup temizliği
- ✅ **SHA256 Password Hash** - Güvenli şifre saklama

### 🎯 Gelişmiş Özellikler
- ✅ **Retry Mekanizması** - Başarısız görevleri tekrar deneme
- ✅ **Task Templates** - Şablonlarla hızlı görev oluşturma
- ✅ **Pause/Resume** - Görevleri duraklat/devam ettir
- ✅ **Bulk Operations** - Toplu görev işlemleri
- ✅ **Export/Import** - Görevleri yedekle/geri yükle
- ✅ **System Tray Support** - Arka planda çalışma
- ✅ **Windows Startup** - Sistem başlangıcında otomatik çalışma
- ✅ **Ultra Compact UI** - Scroll'a gerek yok, her şey görünür!

---

## 📦 Kurulum

### 1. Python Gereksinimi
- Python 3.8 veya üzeri gereklidir
- [Python İndir](https://www.python.org/downloads/)

### 2. Dosyaları Yerleştirme
```
📁 MGD_Scheduler/
├── main.py
├── config.py
├── telegram_manager.py
├── utils.py
├── task_history.py
├── custom_dialogs.py
├── requirements.txt
└── README.md
```

**ÖNEMLİ:** Tüm Python dosyaları aynı klasörde olmalı! Program çalıştığında şu klasör yapısını oluşturacak:

```
📁 MGD_Scheduler/
├── 📄 main.py
├── 📄 config.py
├── ... (diğer .py dosyaları)
├── 📄 config.json          ← Otomatik oluşturulur
├── 📄 tasks.json           ← Otomatik oluşturulur
├── 📁 logs/                ← Otomatik oluşturulur
├── 📁 backups/             ← Otomatik oluşturulur
├── 📁 history/             ← Otomatik oluşturulur
└── 📁 templates/           ← Otomatik oluşturulur
```

### 3. Bağımlılıkları Yükle
```bash
cd MGD_Scheduler
pip install -r requirements.txt
```

### 3. Telegram Bot Kurulumu (ÖNERİLİR - 2 Dakika!)

> ⚠️ **ÖNEMLİ:** Program ilk açılışta Telegram ayarlanmamışsa size soracak!

#### A. Bot Oluşturma (30 saniye)
1. Telegram'da [@BotFather](https://t.me/BotFather) ile konuş
2. `/newbot` komutunu yaz
3. Bot için bir isim ver (örn: "MGD Scheduler Bot")
4. Bot için kullanıcı adı ver (örn: "mgd_scheduler_bot")
5. **Bot Token'ı kopyala** (örn: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### B. Chat ID Öğrenme (30 saniye)
1. Telegram'da [@userinfobot](https://t.me/userinfobot) ile konuş
2. `/start` yaz
3. **Chat ID'yi kopyala** (örn: `123456789`)

#### C. Programda Ayarlama (1 dakika)
1. **Programı başlat:** `python main.py`
2. İlk açılışta **"Telegram'ı şimdi ayarlamak ister misiniz?"** sorusu gelecek
3. **"✅ Şimdi Ayarla"** butonuna tıkla
4. **Bot Token** ve **Chat ID** gir
5. **"Telegram Bildirimlerini Aktif Et"** switch'ini aç ✓
6. **🔍 Bağlantıyı Test Et** butonuna tıkla
   - ✅ Başarılı mesajı gelecek
   - 📱 Telegram'a test mesajı gidecek!
7. **💾 KAYDET** butonuna tıkla

#### ✅ ARTIK HAZIR!
- Görevler başladığında bildirim alacaksınız 🔔
- Görevler tamamlandığında bildirim alacaksınız ✅
- Hata oluşursa bildirim alacaksınız ❌

### 4. İlk Görev Oluşturma
1. **Sol Panel:** "➕ YENİ GÖREV OLUŞTUR" butonuna tıkla
2. **Görev Adı:** Açıklayıcı bir isim gir
3. **Dosya:** Çalıştırılacak dosyayı seç (sürükle-bırak destekli)
4. **Zamanlama:** Başlangıç, bitiş ve frekans ayarla
5. **Kategori & Öncelik:** İsteğe bağlı ayarlar
6. **Kaydet:** "✅ GÖREVİ LİSTEYE EKLE" butonuna tıkla

### Görev Düzenleme
- Görev kartındaki "✏️ Düzenle" butonuna tıkla
- Değişiklikleri yap
- "💾 DEĞİŞİKLİKLERİ KAYDET" ile kaydet

### Görev Duraklat/Devam
- "⏸ Duraklat" butonu ile görevi duraklat
- "▶️ Devam" butonu ile tekrar başlat

### Görev Silme
- "🗑️ Sil" butonuna tıkla
- Onayı doğrula

---

## ⚙️ Ayarlar

### Genel Ayarlar
- **Tema:** Dark/Light mod seçimi
- **Windows Başlangıcı:** Sistem başlangıcında otomatik çalışma
- **Sistem Tepsisi:** Arka planda çalışma

### Telegram Ayarları
- **Bot Token:** Telegram bot token'ınız
- **Chat ID:** Bildirim alacak chat ID
- **Bildirim Tercihleri:**
  - Görev başladığında bildir
  - Görev tamamlandığında bildir
  - Hata olduğunda bildir
  - Retry denemelerinde bildir
  - Günlük rapor gönder

### Gelişmiş Ayarlar
- **Scheduler Interval:** Kontrol sıklığı (saniye)
- **Max Task Timeout:** Maksimum görev süresi
- **Retry Settings:** Tekrar deneme ayarları
- **Backup Settings:** Yedekleme ayarları
- **History Settings:** Geçmiş kayıt ayarları

---

## 📊 Raporlama

### Günlük Rapor
- Telegram üzerinden otomatik günlük rapor
- Toplam çalıştırma, başarı/başarısızlık istatistikleri

### Export İşlemleri
- **Log Export:** CSV formatında log dışa aktarma
- **Task Export:** JSON formatında görev yedekleme
- **History Export:** Geçmiş verilerin dışa aktarılması

---

## 🏥 Hospital Automation Kullanım Örnekleri

### HBYS Veri Aktarımı
```
Görev Adı: HBYS Günlük Veri Senkronizasyonu
Dosya: C:\HBYS\Scripts\daily_sync.py
Kategori: HBYS Entegrasyonu
Öncelik: Kritik
Zamanlama: Her gün 23:00
```

### DICOM Dönüştürme
```
Görev Adı: PDF to DICOM Converter
Dosya: C:\Tools\pdf2dicom.exe
Kategori: DICOM İşlemleri
Öncelik: Yüksek
Zamanlama: Saatte 1 kez
```

### Yedekleme İşlemleri
```
Görev Adı: Database Backup
Dosya: C:\Backup\db_backup.bat
Kategori: Backup/Yedekleme
Öncelik: Kritik
Zamanlama: Her gün 02:00
```

---

## 🔧 Sorun Giderme

### Program Açılmıyor
- Python 3.8+ kurulu mu kontrol et
- `pip install -r requirements.txt` komutunu tekrar çalıştır
- Antivirus programını geçici olarak devre dışı bırak

### Telegram Bildirimleri Gelmiyor
- Bot Token ve Chat ID'yi kontrol et
- [@userinfobot](https://t.me/userinfobot) ile Chat ID'nin doğru olduğunu onayla
- Bot'un aktif olduğundan emin ol
- İnternet bağlantını kontrol et

### Görevler Çalışmıyor
- Dosya yolunun doğru olduğunu kontrol et
- Dosyanın çalıştırma iznine sahip olduğunu kontrol et
- Log dosyalarını incele (`logs/` dizini)

### "Program Zaten Çalışıyor" Hatası
- Görev yöneticisinden tüm python.exe süreçlerini sonlandır
- Sistem tepsisini kontrol et
- Bilgisayarı yeniden başlat

---

## 📁 Dosya Yapısı

```
MGD_Scheduler_v4/
├── main.py                 # Ana program
├── config.py               # Yapılandırma
├── telegram_manager.py     # Telegram entegrasyonu
├── utils.py                # Yardımcı fonksiyonlar
├── task_history.py         # Görev geçmişi yönetimi
├── requirements.txt        # Bağımlılıklar
├── README.md               # Bu dosya
├── tasks.json              # Görev veritabanı (otomatik)
├── config.json             # Ayarlar (otomatik)
├── logs/                   # Log dosyaları
│   ├── mgd_YYYYMMDD.log
│   ├── errors.log
│   └── task_execution.log
├── backups/                # Yedekler
│   └── tasks_backup_*.json
├── templates/              # Görev şablonları
│   └── *.json
└── history/                # Görev geçmişi
    └── history_YYYYMM.json
```

---

## 🤝 Destek & İletişim

**Mustafa GÜNEŞDOĞDU**  
- 🏢 Nazilli Devlet Hastanesi - IT Departmanı
- 💼 Principal Software Architect & Lead UI/UX Designer
- 🏷️ MGdizayn

**Ahmet KAHREMAN (CMX)**  
- 🏢 IT Manager
- 📧 Destek & Yönetim

---

## 📝 Lisans & Kullanım

Bu yazılım Nazilli Devlet Hastanesi IT Departmanı tarafından geliştirilmiştir.  
Kurumsal kullanım içindir.

**© 2025 MGdizayn - Mustafa GÜNEŞDOĞDU**  
**be-original** 🎯

---

## 🔄 Sürüm Geçmişi

### v4.0 (Ocak 2025)
- ✨ Telegram bot entegrasyonu
- ✨ Task kategorileri ve öncelik seviyeleri
- ✨ Detaylı task history sistemi
- ✨ Dark/Light theme desteği
- ✨ Task şablonları
- ✨ Gelişmiş ayarlar menüsü
- 🐛 Çoklu bug fix ve performans iyileştirmeleri

### v3.5 (Aralık 2024)
- ✨ Worker mode izolasyonu
- ✨ Atomic file operations
- ✨ Auto backup sistemi
- ✨ Retry mekanizması

### v3.0 (Kasım 2024)
- ✨ İlk stabil sürüm
- ✨ Temel zamanlama özellikleri
- ✨ System tray desteği

---

## 💡 İpuçları

1. **Kritik Görevler:** Hastane işlemleri için önceliği "Kritik" yapın
2. **Telegram Notifications:** Kritik görevlerde mutlaka aktif edin
3. **Backup:** Düzenli olarak görevleri export edin
4. **Log İnceleme:** Sorun yaşarsanız log dosyalarını inceleyin
5. **Test:** Yeni görevleri önce test modunda çalıştırın

---

**🏥 Hospital Automation - Sağlık Hizmetlerinde Otomasyon** 🚀
