# TEFAS Rapor Workflow Kılavuzu

## 🔄 İki Çalışma Modu

### 🤖 Otomatik Çalışma
**Ne zaman:** Her iş günü (Pazartesi-Cuma) **Türkiye saati 09:30**da
**Ne yapar:**
- ✅ TEFAS verilerini analiz eder
- ✅ Excel ve HTML raporu oluşturur  
- ✅ Email ile raporları gönderir
- ✅ Dosyaları repository'ye kaydeder

### 👆 Manuel Çalışma
**Ne zaman:** İstediğiniz herhangi bir zamanda
**Nasıl:** GitHub'da Actions sekmesinden tetikleme

---

## 🎯 Manuel Nasıl Çalıştırılır

### Adım Adım:
1. **GitHub'da repository'nize gidin** (`tefastrend`)
2. Üst menüden **"Actions"** sekmesine tıklayın
3. Sol menüden **"Daily TEFAS Report"** workflow'unu seçin
4. Sağ tarafta **yeşil "Run workflow"** butonuna tıklayın
5. Açılan dropdown'da tekrar **"Run workflow"** butonuna tıklayın
6. ✅ İşlem başladı! 2-3 dakikada tamamlanır

### 📱 Mobil'den Manuel Çalıştırma:
1. GitHub Mobile app veya mobil browser
2. Repository → Actions → Daily TEFAS Report
3. "Run workflow" butonuna tap
4. Confirm ile çalıştır

---

## 🕐 Zamanlama Detayları

### Otomatik Çalışma Saatleri:
- **Pazartesi**: 09:30 ✅
- **Salı**: 09:30 ✅  
- **Çarşamba**: 09:30 ✅
- **Perşembe**: 09:30 ✅
- **Cuma**: 09:30 ✅
- **Cumartesi**: Çalışmaz ❌
- **Pazar**: Çalışmaz ❌

### Manuel Çalışma:
- **Her gün**: 24/7 istediğiniz zaman ⏰
- **Sınırsız**: Günde istediğiniz kadar çalıştırabilirsiniz
- **Anında**: Butona bastıktan 30 saniye içinde başlar

---

## 📊 Çalışma Durumunu Takip Etme

### Status İkonları:
- 🟡 **Sarı nokta**: Çalışıyor (running)
- ✅ **Yeşil tik**: Başarılı (success)  
- ❌ **Kırmızı X**: Hata (failed)
- ⏸️ **Gri**: Beklemede (pending)

### Detaylı Logs Görme:
1. Actions sekmesinde workflow'a tıklayın
2. **"generate-report"** job'ına tıklayın
3. Her adımı açıp detayları görebilirsiniz:
   - **Run TEFAS analysis**: Analiz logs'u
   - **Generate Email Report**: Email gönderim durumu
   - **Commit generated files**: Dosya kaydetme

---

## 🚨 Hata Durumları

### Email Gönderilmiyorsa:
1. **Secrets kontrol**: SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL var mı?
2. **Gmail App Password**: Doğru 16 haneli şifre mi?
3. **Logs inceleme**: "Generate Email Report" adımında hata var mı?

### Analiz Çalışmıyorsa:
1. **İnternet bağlantısı**: TEFAS API erişilebilir mi?
2. **Veri durumu**: Hafta sonu/tatil günü veri var mı?
3. **Rate limiting**: Çok sık çalıştırılmış mı?

---

## 🎯 Kullanım Senaryoları

### Günlük Kullanım:
- ✨ **Hiçbir şey yapma**: Otomatik 09:30'da gelir
- 🍵 **Kahve molasında kontrol**: Email geldi mi?

### Acil Analiz:
- 📈 **Piyasa hareketliliği**: Manuel tetikle, 3 dakikada rapor al
- 🔍 **Ekstra kontrol**: Gün içinde istediğin kadar çalıştır

### Hafta Sonu:
- 💤 **Otomatik çalışmaz**: Hafta sonları veri yok
- 👆 **Manuel çalıştırabilir**: Test için veya özel durum

---

## ⚡ Pro İpuçları

### Hız:
- 🚀 **Manual trigger**: 30 saniye başlama süresi
- ⚙️ **Total süre**: 2-3 dakika (analiz + email)
- 📊 **Simultaneous**: Birden fazla paralel çalıştırılabilir

### Zamanlama:
- ⏰ **09:30 optimal**: Piyasa açılış öncesi fresh data
- 🎯 **Manuel trigger**: Piyasa saatleri içinde güncel analiz
- 📅 **Hafta içi focus**: Veri en güvenilir

### Monitoring:
- 📧 **Email success**: Logs'ta "✅ Email başarıyla gönderildi" mesajı
- 📁 **File updates**: Repository'de yeni Excel/JSON dosyaları
- 🔔 **GitHub notifications**: Başarısız runs için bildirim

---

## 🎊 Özet

**Süper Basit:**
1. **Kurulum bitince**: Her sabah 09:30'da otomatik email gelir
2. **Acil durum**: Actions → Run workflow → 3 dakikada rapor
3. **Zero maintenance**: Bir kez ayarladıktan sonra kendi kendine çalışır

**En İyi Deneyim:**
- 🌅 **Sabah**: Otomatik raporu kontrol et
- 📈 **Gün içi**: İhtiyaç halinde manuel tetikle  
- 💤 **Hafta sonu**: Sistem dinlenir, sen de dinlen

**Sistem tamamen hazır! 🚀**