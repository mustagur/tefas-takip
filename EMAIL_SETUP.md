# Gmail SMTP Email Kurulumu

Bu dosya, TEFAS raporlarının Gmail üzerinden otomatik olarak nasıl gönderilebileceğini açıklar.

## ⚡ Hızlı Kurulum Özeti

**🔥 Sadece 3 Adım:**
1. **Gmail'de**: Güvenlik → 2 Adımlı Doğrulama → Uygulama şifreleri → E-posta → TEFAS-Reports
2. **GitHub'da**: Settings → Secrets and variables → Actions → 3 secret ekle
3. **Test**: Actions → Daily TEFAS Report → Run workflow

**✨ Sonuç**: Her gün 09:30'da mailbox'a TEFAS raporu gelecek!

## 🛠️ Kurulum Adımları

### 1. Gmail App Password Oluşturma

#### Adım 1: İki Faktörlü Doğrulama Aktifleştirme
1. Gmail hesabınızda **İki Faktörlü Doğrulama** aktif olmalı
2. Google hesabınıza gidin: https://myaccount.google.com/
3. Sol menüden **"Güvenlik"** sekmesine tıklayın
4. **"Google'da oturum açma"** bölümünde **"2 Adımlı Doğrulama"** seçin
5. Eğer aktif değilse **"Başlayın"** butonuna tıklayın ve kurulumu tamamlayın

#### Adım 2: Uygulama Şifresi Oluşturma
1. İki faktörlü doğrulama aktifken, aynı sayfada **"Uygulama şifreleri"** seçeneğine tıklayın
2. **"Uygulama seçin"** dropdown'dan **"E-posta"** seçin
3. **"Cihaz seçin"** dropdown'dan **"Diğer (özel ad)"** seçin
4. Açılan kutucuğa **"TEFAS-Reports"** yazın
5. **"Oluştur"** butonuna tıklayın
6. Oluşturulan 16 haneli şifreyi kaydedin (örnek: `abcd efgh ijkl mnop`)
7. **"Bitti"** butonuna tıklayın

**🔍 Türkçe Menü İsimleri:**
- Güvenlik = Security
- 2 Adımlı Doğrulama = 2-Step Verification  
- Uygulama şifreleri = App passwords
- E-posta = Mail
- Diğer (özel ad) = Other (custom name)
- Oluştur = Generate

### 2. GitHub Secrets Ayarlama

#### Adım 1: Repository Ayarlarına Gitme
1. GitHub'da **tefastrend** repository'nize gidin
2. Repository sayfasında üst menüden **"Settings"** (Ayarlar) sekmesine tıklayın
3. Sol menüden **"Secrets and variables"** seçeneğine tıklayın
4. Açılan alt menüden **"Actions"** seçin

#### Adım 2: Secrets Ekleme
Her bir secret için şu adımları tekrarlayın:

1. **"New repository secret"** (Yeni repository secret'i) butonuna tıklayın
2. **İlk Secret (SMTP_USER):**
   - **Name**: `SMTP_USER`
   - **Secret**: `melihekmekci1@gmail.com`
   - **"Add secret"** butonuna tıklayın
3. **İkinci Secret (SMTP_PASSWORD):**
   - **"New repository secret"** butonuna tekrar tıklayın
   - **Name**: `SMTP_PASSWORD`
   - **Secret**: `abcd efgh ijkl mnop` (yukarıda oluşturduğunuz 16 haneli app password)
   - **"Add secret"** butonuna tıklayın

4. **Üçüncü Secret (RECIPIENT_EMAIL):**
   - **"New repository secret"** butonuna tekrar tıklayın
   - **Name**: `RECIPIENT_EMAIL`
   - **Secret**: 
     - **Tek kişi**: `melihekmekci1@gmail.com`
     - **Çoklu kişi**: `email1@gmail.com, email2@yahoo.com, email3@hotmail.com`
   - **"Add secret"** butonuna tıklayın

**📌 Çoklu Alıcı Örneği:**
```
RECIPIENT_EMAIL = melihekmekci1@gmail.com, arkadas@gmail.com, patron@sirket.com
```
**Sonuç**: 3 kişi aynı anda rapor alacak (1. kişi TO, diğerleri CC)

**🔍 GitHub'da Tıklanacak Yerler:**
- Settings = Repository üst menüsünden "Settings"
- Secrets and variables = Sol menüden
- Actions = Secrets and variables altından
- New repository secret = Yeşil buton
- Add secret = Secret ekleme sayfasında mavi buton

### 3. GitHub Actions Tetikleme ve Test

#### Manuel Test (Hemen Test Etmek İçin)
Secrets eklendikten sonra:

1. GitHub repository sayfanızda üst menüden **"Actions"** sekmesine tıklayın
2. Sol taraftan **"Daily TEFAS Report"** workflow'unu seçin
3. Sağ tarafta **"Run workflow"** (Workflow çalıştır) butonuna tıklayın
4. Açılan pencerede **"Run workflow"** butonuna tekrar tıklayın
5. 🟢 Yeşil check işareti çıkana kadar bekleyin (2-3 dakika sürer)
6. Workflow'a tıklayıp **"Generate Email Report"** adımını açın
7. Logs'ta **"✅ Email başarıyla gönderildi!"** mesajını görüyorsanız başarılı!

#### Otomatik Çalışma
- **Zaman**: Her iş günü UTC 06:30'da (Türkiye saati 09:30)
- **Günler**: Pazartesi - Cuma
- **Hafta sonları**: Çalışmaz

**🔍 GitHub Actions'da Tıklanacak Yerler:**
- Actions = Repository üst menüsünden
- Daily TEFAS Report = Sol menüden workflow seçimi
- Run workflow = Sağ tarafta mavi buton
- Generate Email Report = Workflow detayında adım ismi

## 📧 Email İçeriği

Gönderilecek email şu ekleri içerir:
- **Excel Raporu**: Detaylı analiz tabloları
- **HTML Raporu**: Web formatında görsel rapor

## 🔍 Sorun Giderme (Troubleshooting)

### 🚨 Email Gelmiyorsa

**1. GitHub Actions Logs'unu Kontrol Edin:**
- Repository'de **Actions** sekmesine gidin
- En son çalışan workflow'a tıklayın
- **"Generate Email Report"** adımına tıklayın
- Logs'ta hata mesajı var mı bakın

**2. Secrets'ları Kontrol Edin:**
- Settings > Secrets and variables > Actions sayfasına gidin
- Şu 3 secret'in var olduğunu kontrol edin:
  - `SMTP_USER`
  - `SMTP_PASSWORD` 
  - `RECIPIENT_EMAIL`
- Eğer yanlış girildiyse, secret'a tıklayıp **"Update"** ile düzeltebilirsiniz

**3. Gmail App Password'u Kontrol Edin:**
- 16 haneli şifre doğru mu?
- İki faktörlü doğrulama aktif mi?
- Gmail hesabında "Güvenlik" > "Uygulama şifreleri"'nde TEFAS-Reports görüyor musunuz?

**4. Spam/Çöp Kutusunu Kontrol Edin:**
- Gmail'de spam klasörüne bakın
- "TEFAS Günlük Rapor" başlıklı email arıyın

### 🔄 Simülasyon Modu
Eğer SMTP secrets'ları ayarlanmamışsa:
- ⚠️ **"SMTP credentials bulunamadı - Simülasyon modu"** mesajı görürsünüz
- Email içeriği sadece GitHub logs'una yazdırılır
- Rapor dosyaları repository'de saklanır ama email gönderilmez
- Bu durumda yukarıdaki "Secrets Ayarlama" adımlarını tekrar yapın

### ✅ Başarılı Gönderim Mesajları
**Logs'ta görmek istediğiniz mesajlar:**
```
✅ SMTP credentials bulundu - Gerçek email gönderimi aktif
📧 Gönderici: melihekmekci1@gmail.com
📧 Gmail SMTP ile email gönderiliyor...
✅ Email başarıyla gönderildi!
📧 Message ID: smtp_20251013_0930
📧 Alıcı: melihekmekci1@gmail.com
```

## 📊 Test Etme

Local test için:
```bash
export SMTP_USER="your_email@gmail.com"
export SMTP_PASSWORD="your_app_password"  
export RECIPIENT_EMAIL="recipient@gmail.com"
python upload_to_sheets.py
```

## 🔐 Güvenlik

- Gmail App Password kullanın, asla gerçek şifrenizi GitHub'da saklamayın
- Secrets GitHub tarafından şifrelenir ve sadece Actions sırasında kullanılır
- App Password istediğiniz zaman iptal edebilirsiniz

## 📝 Alıcı Email Değiştirme

### 🔄 Tek Alıcı Değiştirme
1. GitHub repository'de **Settings** → **Secrets and variables** → **Actions**
2. **RECIPIENT_EMAIL** secret'ina tıklayın
3. **"Update"** butonuna tıklayın
4. Yeni email adresini yazın: `yeni.email@gmail.com`
5. **"Update secret"** butonuna tıklayın
6. **Actions** → **Run workflow** ile test edin

### 💫 Çoklu Alıcı Ekleme
1. Aynı şekilde **RECIPIENT_EMAIL** secret'ini güncelleyin
2. Virgülle ayırarak yazın: 
   ```
   melihekmekci1@gmail.com, arkadas@gmail.com, patron@sirket.com
   ```
3. İlk email ana alıcı (TO), diğerleri kopya (CC) olur
4. Test edin - tüm alıcılar email alacak

### 🎯 Örnek Senaryolar

**Sadece siz:**
```
RECIPIENT_EMAIL = melihekmekci1@gmail.com
```

**Siz + 1 kişi:**
```
RECIPIENT_EMAIL = melihekmekci1@gmail.com, arkadas@yahoo.com
```

**Takım (3+ kişi):**
```
RECIPIENT_EMAIL = melih@gmail.com, ali@yahoo.com, ayse@hotmail.com, patron@sirket.com
```

### ⚡ İpuçları
- 🚫 Email adreslerinde boşluk bırakmayın (sistem otomatik temizler)
- ✅ Gmail, Yahoo, Hotmail gibi tüm servisler çalışır  
- 📊 Maksimum 10 alıcı önerilir (spam engelini aşmamak için)
- 📋 Secret değiştirdikten sonra hemen test edebilirsiniz
- 🔄 İstediğiniz zaman tekrar değiştirebilirsiniz
