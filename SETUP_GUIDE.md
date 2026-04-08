# 🚀 TEFAS Otomatik Rapor Sistemi - Kurulum Rehberi

Bu rehber, TEFAS analiz raporlarınızı her iş günü otomatik olarak oluşturup Google Sheets ve GitHub Pages'te yayınlayan sistemi kurmak için gerekli adımları içerir.

## 📋 Genel Bakış

**Sistem şunları yapar:**
- ⏰ Her iş günü saat 09:30'da otomatik çalışır
- 📊 TEFAS verilerini analiz eder
- 📄 HTML ve Excel raporları oluşturur
- 📋 Dosyaları repository'de saklar
- 📊 GitHub Actions log'larında rapor detaylarını gösterir

## 🔧 Kurulum Adımları

### 1. GitHub Repository Hazırlığı

```bash
# Repository'yi GitHub'a push edin
git add .
git commit -m "TEFAS otomatik rapor sistemi kurulumu"
git push origin main
```

### 2. Basit Kurulum - API Gerekmez!


### 3. Portfolio Fonlarınızı Ayarlayın

`tefas_panel.json` dosyasını düzenleyip portföy fonlarınızı ekleyin:

```json
{
  "portfolio_funds": ["DFI", "TLY", "YBS", "ZPX"],
  "early_momentum_candidates": [],
  "trend_candidates": [],
  "last_updated": "2024-01-01",
  "tracking_settings": {
    "early_momentum_min_score": 1.5,
    "trend_min_score": 3.0,
    "portfolio_alert_threshold": 1.5
  }
}
```

## 🚀 Test ve Çalıştırma

### Manuel Test
GitHub Actions'ı manuel olarak çalıştırmak için:
1. Repository'nizde **Actions** tab'ine gidin
2. **Daily TEFAS Report** workflow'unu seçin
3. **Run workflow > Run workflow** tıklayın

### Otomatik Çalışma
- Her iş günü (Pazartesi-Cuma) UTC 06:30'da (Türkiye saati 09:30) otomatik çalışır
- İlk çalışmadan sonra email raporu: melihekmekci1@gmail.com'a otomatik gönderilir

## 📊 Email Raporları

Sistem kurulumu tamamlandıktan sonra:

- Her çalışmadan sonra melihekmekci1@gmail.com adresine Excel ve HTML dosyaları ekleri olarak gönderilir
- Email'de detaylı analiz özeti ve açıklamalar bulunur
- Raporlar her iş günü saat 09:30'da otomatik olarak hazırlanır

## 🔧 Sorun Giderme

### Common Issues

#### 1. Gmail API Hatası
```
Error 403: Forbidden
```
**Çözüm:** Google Cloud Console'da Gmail API'nin etkinleştirildiğinden emin olun.

#### 2. Email Gönderme Hatası
**Çözüm:** Service Account'un Gmail API erişim iznine sahip olduğundan ve domain-wide delegation yapılıp yapılmadığını kontrol edin.

### Debug

GitHub Actions log'larını kontrol etmek için:
1. **Actions** tab > **Daily TEFAS Report** workflow
2. En son çalıştırılan job'a tıklayın
3. Her step'in detaylarını inceleyin

## 📈 Özelleştirmeler

### Çalışma Zamanını Değiştirme
`.github/workflows/daily-report.yml` dosyasında:
```yaml
schedule:
  - cron: '30 6 * * 1-5'  # UTC 06:30 = TR 09:30
```

### Fon Sayısını Artırma
`tefas_trend.py` dosyasında:
```python
MAX_CODES = 100  # İstediğiniz sayı
```

### Analiz Parametreleri
`tefas_trend.py` dosyasında puanlama kriterlerini değiştirebilirsiniz.

---

## 📞 Destek

Kurulum sırasında sorun yaşarsanız:
1. GitHub Issues bölümünde soru açın
2. Log dosyalarını paylaşın
3. Hata mesajlarını tam metin olarak ekleyin

## 🔒 Güvenlik Notları

- Service Account JSON dosyasını asla repository'ye commit etmeyin
- GitHub Secrets kullanarak credentials'ları güvenli tutun
- Service Account'a minimum gerekli yetkileri verin
- Google Sheets'i sadece "reader" olarak herkese açık yapın

---

**✅ Kurulum tamamlandı! Artık her iş günü otomatik raporlarınız hazır olacak.**