# Smart Duplicate Cleaner Pro

**Gelişmiş Kopya Dosya Bulucu ve Temizleyici (SHA-256 Hash Tabanlı)** ✅

Modern, performans odaklı ve kullanıcı dostu arayüzlü Python/Tkinter uygulaması. Seçilen klasördeki kopya dosyaları SHA-256 hash ile tespit eder, gruplar halinde gösterir ve güvenli silme sağlar.

---

## ✨ Yeni Özellikler (Pro Sürüm)

### Performans İyileştirmeleri
- **Çoklu Thread Hash Hesaplama**: `ThreadPoolExecutor` ile 4 worker thread (ayarlar.json'dan değiştirilebilir)
- **Paralel İşleme**: Dosyalar batch'ler halinde hashlenir, UI donmaz
- **Lazy Loading**: Grup detayları sadece genişletildiğinde yüklenir (binlerce dosyada anında açılış)
- **Akıllı Tarama**: Önce boyut filtresi, sonra sadece adayları hashler
- **Progress Batching**: Her dosyada değil, batch'lerde UI güncellemesi

### Kullanıcı Deneyimi (UX)
- **Grup Yapısı**: Kopya dosyalar expandable grup halinde listelenir
- **Önizleme Paneli**: Sağ tarafta resim/metin dosyaları anlık önizleme
- **Otomatik Seçim Stratejileri**:
  - 📅 En Eskiyi Tut / En Yeniyi Tut
  - 📏 En Kısa Yolu Tut
  - 📂 Aynı Klasördekini Tut
- **Modern UI**: Paned window, stilli butonlar, durum çubuğu, istatistikler
- **Sağ Tık Menüsü**: Konumu aç, özellikler, hızlı işaretle
- **Dışa Aktar**: JSON / CSV formatında rapor alma

### Güvenlik ve Kolaylık
- Ayarlar ototmatik kaydedilir (`settings.json`)
- Son açılan klasör hatırlanır
- Silme onayı ile koruma
- Boş dosyalar atlanır
- Hata toleranslı dosya okuma

---

## 🔧 Gereksinimler

- **Python 3.8+** (tested with 3.12+)
- **Tkinter** (Windows'ta dahili, Linux'ta: `sudo apt install python3-tk`)
- **Pillow** (opsiyonel, resim önizleme için): `pip install Pillow`

---

## 🚀 Kurulum ve Çalıştırma

```bash
# Depoyu klonlayın
git clone <repo-url>
cd Smart-Duplicate-Cleaner

# Opsiyonel: resim önizleme için
pip install -r requirements.txt

# Uygulamayı çalıştırın
python main.py
```

---

## 🖱️ Kullanım Kılavuzu

| Adım | Açıklama |
|------|----------|
| 1 | **📁 Klasör Seç** butonla taranacak kök klasörü belirleyin |
| 2 | **▶ Taramayı Başlat** ile tarama başlar (progress bar ile izleyin) |
| 3 | Sol panelde **grup başlıklarını** (▶) tıklayarak dosyaları görün |
| 4 | Sağ panelde **önizleme** için dosyaya tıklayın |
| 5 | **☑/☐** ile silinecekleri işaretleyin veya **Otomatik Seçim** butonlarını kullanın |
| 6 | **🗑 Seçilileri Sil** → Onayla → İşlem tamam |
| 7 | İsterseniz **📤 Dışa Aktar** ile rapor kaydedin |

### Otomatik Seçim Stratejileri
| Buton | Davranış |
|-------|----------|
| 📅 En Eskiyi Tut | Her gruptan en eski dosya (mtime) korunur |
| 📅 En Yeniyi Tut | Her gruptan en yeni dosya korunur |
| 📏 En Kısa Yolu Tut | En kısa yol uzunluğundaki dosya korunur |
| 📂 Aynı Klasörde Tut | Grupın çoğunluğunun olduğu klasördeki dosya korunur |

---

## ⚙️ Ayarlar (`settings.json`)

Otomatik oluşturulur, manuel de düzenlenebilir:

```json
{
  "hash_workers": 4,        // Paralel hash thread sayısı (CPU çekirdeğinize göre ayarlayın)
  "chunk_size": 65536,      // Hash okuma parça boyutu (bayt)
  "last_folder": "C:/Users/..."  // Son açılan klasör
}
```

**Performans İpuçları:**
- SSD için `hash_workers: 8`, HDD için `2-4` önerilir
- Büyük dosyalar (>1GB) için `chunk_size: 1048576` (1MB) hızlandırabilir

---

## 💡 Nasıl Çalışır?

1. **Boyut Filtresi**: Tüm dosyalar boyutlarına göre gruplanır, tekil boyutlu dosyalar elenir
2. **Paralel Hash**: Kalan aday dosyalar `ThreadPoolExecutor` ile SHA-256 hesaplanır
3. **Grup Oluşturma**: Aynı `(boyut, hash)` çiftine sahip dosyalar kopya grubu yapar
4. **Lazy UI**: Gruplar ağaç yapısında gösterilir, detaylar genişletince yüklenir
5. **Güvenli Silme**: Kullanıcı onayıyla `os.remove()` ile kalıcı silme

---

## ⚠️ Güvenlik ve Uyarılar

> 🚨 **BU UYGULAMA DOSYALARI KALICI OLARAK SİLER (GERİ ALINAMAZ)** 🚨
>
> - **Her zaman ÖNEMLİ VERİLERİNİZİ YEDEKLEYİN** bu aracı kullanmadan önce
> - **Yazar HERHANGİ BİR VERİ KAYBI SORUMLULUĞU KABUL ETMEZ**
> - **KULLANIM KENDİ RİSKİNİZDEDİR**
>
> **Öneri:** Önce tarama yapın, kopya grupları ve önizlemeleri dikkatle inceleyin, ardından silme işlemini onaylayın.

---

## 🐛 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| `tkinter` hatası / GUI açılmıyor | Linux: `sudo apt install python3-tk` |
| Resim önizleme çalışmıyor | `pip install Pillow` |
| Tarama çok yavaş | `settings.json` → `hash_workers` artırın (SSD: 8, HDD: 4) |
| Bellek hatası (çok büyük klasör) | `chunk_size` küçültün, `hash_workers` azaltın |
| Ağ sürücüsünde donuyor | Yerel kopyalayın, sonra tarayın |

---

## 🤝 Katkıda Bulunma

Katkılar, hata raporları ve öneriler **Pull Request** veya **Issue** ile memnuniyetle karşılanır.

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Push yapın (`git push origin feature/yeni-ozellik`)
5. Pull Request açın

---

## 📄 Lisans

MIT Lisansı. Detaylar için `LICENSE` dosyasına bakın.

---

## 📝 Değişiklik Geçmişi

### v2.0 (Pro) - 2026
- ✅ Çoklu thread hash hesaplama (ThreadPoolExecutor)
- ✅ Lazy loading grup yapısı
- ✅ Önizleme paneli (resim/metin)
- ✅ Otomatik seçim stratejileri (4 adet)
- ✅ Modern paned UI, sağ tık menüsü
- ✅ JSON/CSV dışa aktarım
- ✅ Ayarlar kalıcılığı (settings.json)
- ✅ Progress batching, donma sorunu çözüldü
- ✅ Boşluk tasarrufu hesaplama ve sıralama

### v1.0 - Temel Sürüm
- Basit tkinter GUI
- Tek thread hash
- Düz liste görünümü
- Temel silme işlevi