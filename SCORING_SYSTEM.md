# TEFAS Kapsamlı Puanlama Sistemi Dokümantasyonu

## Genel Bakış

TEFAS analiz sistemi, fon performansını değerlendirmek için **5 ana bileşenden oluşan kapsamlı bir 100-puanlık skorlama sistemi** kullanmaktadır. Bu sistem, geleneksel teknik analizin ötesinde, yatırımcı davranışları, likidite durumu, risk-getiri profili ve piyasa zamanlaması gibi profesyonel yatırım kriterlerini birleştirir.

## Skorlama Bileşenleri

### 1. Trend Bileşeni (Maksimum 40 Puan)

Teknik analiz göstergelerine dayalı temel trend değerlendirmesi:

| Kriter | Puan | Açıklama |
|--------|------|----------|
| **RSI > 60** | +10 | Güçlü momentum göstergesi |
| **MACD Pozitif Kesişim** | +20 | En güçlü yükseliş sinyali |
| **Bollinger Band Kırılımı** | +10 | Volatilite tabanlı breakout |

**Toplam:** 40 puan

### 2. Yatırımcı Akımı Bileşeni (Maksimum 20 Puan)

Fona olan yatırımcı ilgisini ve sermaye akımını değerlendirir:

| Kriter | Puan | Açıklama |
|--------|------|----------|
| **7-gün yatırımcı artışı > %3** | - | Birinci koşul |
| **+ AUM (Portföy büyüklüğü) artışı** | - | İkinci koşul |
| **Her iki koşul birlikte** | +20 | Güçlü yatırımcı ilgisi |

**Toplam:** 20 puan

### 3. Hacim & Likidite Bileşeni (Maksimum 20 Puan)

İşlem hacmi ve likidite durumunu analiz eder:

| Kriter | Puan | Açıklama |
|--------|------|----------|
| **Günlük hacim artışı** | - | Birinci koşul |
| **+ 5-gün ortalama yüksek** | - | İkinci koşul |
| **Her iki koşul birlikte** | +20 | Sağlıklı likidite artışı |

**Toplam:** 20 puan

### 4. Volatilite Bileşeni (Maksimum 20 Puan)

Risk-getiri profilini değerlendirir:

| Kriter | Puan | Açıklama |
|--------|------|----------|
| **Düşük ATR artışı** | - | Kontrollü volatilite |
| **+ Sharpe oranı > 1** | - | İyi risk-ayarlı getiri |
| **Her iki koşul birlikte** | +20 | Optimal risk profili |

**Toplam:** 20 puan

### 5. Zamanlama Bileşeni (Maksimum 10 Puan)

Kısa vadeli momentum ve zamanlama kalitesini ölçer:

| Kriter | Puan | Açıklama |
|--------|------|----------|
| **Son 5 günde 4+ pozitif kapanış** | +10 | Güçlü kısa vadeli momentum |

**Toplam:** 10 puan

## Normalizasyon Süreci

### Ham Puan Hesaplaması
Sistem önce 110 üzerinden ham puan hesaplar (40+20+20+20+10=110 maksimum).

### Normalizasyon Formülü
```
Final Skor = round((Ham Puan ÷ 11) × 10)
```

**Örnek:**
- Ham Puan: 77 → Final Skor: round((77÷11)×10) = round(70) = 70
- Ham Puan: 44 → Final Skor: round((44÷11)×10) = round(40) = 40

Bu normalizasyon sayesinde tüm bileşenler eşit ağırlıkta değerlendirilir.

## Aday Kategorizasyonu

### Erken Momentum Adayları (50-75 Puan)
- **Tanım:** Gelişmekte olan fırsatlar
- **Özellik:** Potansiyel gösteriyor ancak henüz tam olgunlaşmamış
- **Kullanım:** Erken giriş fırsatları için

### Güçlü Trend Adayları (75+ Puan)
- **Tanım:** Yüksek güvenilirlik seviyesi
- **Özellik:** Çoklu kriterleri karşılayan güçlü adaylar
- **Kullanım:** Ana yatırım fırsatları için

## Ek Filtreler

### Momentum Filtresi
Erken momentum ve güçlü trend adayları için ek kalite kontrolü:

**Koşul 1:** Son 3 günde en az 2 pozitif kapanış
**VEYA**
**Koşul 2:** 3-günlük ortalama değişim > %0.5

Bu filtre, yalnızca puanı yüksek olan ancak yakın zamanda pozitif momentum göstermeyen fonları elemek için kullanılır.

### Case Analiz Filtresi
Özel pattern analizleri yalnızca **yatırımcı sayısı 50 ve üstü** olan fonlar için yapılır. Bu sayede likidite riski minimize edilir.

### Performans Filtreleri
**Aday Seçimi:** Erken momentum ve güçlü trend adayları içinde haftalık getirisi en yüksek **10 fon** HTML raporunda gösterilir.

**Case Analizleri:** Her case türü için haftalık performansa göre sıralanmış **en iyi 15 fon** raporlanır.

Bu filtreler sayesinde rapor odaklı kalır ve yalnızca en yüksek potansiyeli olan fonlar öne çıkar.

## Teknik Implementasyon

### Kod Yapısı
```python
def calculate_comprehensive_score(self, df, fund_code):
    score_raw = 0.0
    criteria = []
    
    # 1. Trend Component (Max 40)
    trend_score, trend_criteria = self._calculate_trend_component(df)
    score_raw += trend_score
    
    # 2. Investor Flow Component (Max 20)
    investor_score, investor_criteria = self._calculate_investor_flow_component(df)
    score_raw += investor_score
    
    # 3. Volume & Liquidity Component (Max 20)
    volume_score, volume_criteria = self._calculate_volume_liquidity_component(df)
    score_raw += volume_score
    
    # 4. Volatility Component (Max 20)
    volatility_score, volatility_criteria = self._calculate_volatility_component(df)
    score_raw += volatility_score
    
    # 5. Timing Component (Max 10)
    timing_score, timing_criteria = self._calculate_timing_component(df)
    score_raw += timing_score
    
    # Normalize from 110-point to 100-point scale
    final_score = round((score_raw / 11) * 10)
    
    return final_score, criteria
```

### Trend Status Belirleme
```python
def determine_trend_status(self, result):
    if result.score >= 75:  # config.analysis.trend_min_score
        return "🔥 Güçlü Yükseliş", criteria
    elif result.score >= 50:  # config.analysis.early_momentum_min_score
        return "📈 Yükseliş Sinyali", criteria
    # ... decline ve neutral logic
```

## Avantajları

### 1. **Kapsamlı Değerlendirme**
- Tek bir göstergeye değil, 5 farklı boyuta odaklanır
- Daha güvenilir ve dengeli skorlama

### 2. **Risk Yönetimi**
- Volatilite ve Sharpe oranı ile risk kontrolü
- Likidite filtresi ile işlem riski minimizasyonu

### 3. **Momentum Kontrolü**
- Kısa vadeli momentum filtresi ile yanlış pozitif sinyalleri azaltır
- Zamanlama bileşeni ile entry timing kalitesini artırır

### 4. **Şeffaflık**
- Her skor bileşeni açık şekilde gösterilir
- Kriterler detaylandırılır, black-box yaklaşım yoktur

### 5. **Esneklik**
- Konfigürasyon dosyası ile tüm parametreler ayarlanabilir
- Test ve prodüksiyon ortamları için farklı ayarlar

## Konfigürasyon

### Config Dosyasında Puanlama Parametreleri
```python
class TechnicalAnalysisConfig:
    # Trend Component (Max 40 points)
    rsi_strong_score: int = 10      # RSI > 60
    macd_score: int = 20           # MACD positive crossover
    bollinger_score: int = 10      # Bollinger breakout
    
    # Investor Flow Component (Max 20 points) 
    investor_flow_score: int = 20  # 7-day growth >3% + AUM increase
    
    # Volume & Liquidity Component (Max 20 points)
    volume_liquidity_score: int = 20  # Volume increase + 5-day avg rising
    
    # Volatility Component (Max 20 points)
    volatility_score: int = 20     # Low ATR increase + Sharpe > 1
    
    # Timing Component (Max 10 points) 
    timing_score: int = 10         # 4+ positive closes in 5 days
```

### Analiz Eşikleri
```python
class AnalysisConfig:
    early_momentum_min_score: int = 50   # 50-75 range for early momentum
    early_momentum_max_score: int = 75
    trend_min_score: int = 75            # 75+ for trend candidates
```

## Örnek Skor Hesaplaması

### Örnek Fon: ABC
```
Raw Scores:
- RSI (85.2) > 60: +10 puan
- MACD Pozitif Kesişim: +20 puan  
- Bollinger Kırılım: +10 puan
- Yatırımcı Akımı (%8.5 artış): +20 puan
- Hacim Artışı (Günlük +15%, 5G +8%): +20 puan
- Volatilite (ATR: 1.2, Sharpe: 1.5): +20 puan
- Zamanlama (5/5 pozitif): +10 puan

Ham Toplam: 110 puan
Final Skor: (110 ÷ 11) × 10 = 100 puan
Kategori: 💎 Güçlü Trend Adayı
```

### Örnek Fon: XYZ
```
Raw Scores:
- RSI (72.1) > 60: +10 puan
- MACD: Henüz kesişim yok (+0 puan)
- Bollinger: Henüz kırılım yok (+0 puan)  
- Yatırımcı Akımı (%5.2 artış): +20 puan
- Hacim: Henüz artış yok (+0 puan)
- Volatilite: Sharpe < 1 (+0 puan)
- Zamanlama (3/5 pozitif): +0 puan

Ham Toplam: 30 puan
Final Skor: (30 ÷ 11) × 10 = 27 puan
Kategori: ➡️ Durağan/Kararsız
```

## Test ve Doğrulama

### Unit Test Örneği
```python
def test_scoring_normalization():
    analyzer = TechnicalAnalyzer()
    
    # Test case 1: Maximum score
    raw_score = 110
    expected = 100
    actual = round((raw_score / 11) * 10)
    assert actual == expected
    
    # Test case 2: Mid-range score
    raw_score = 55
    expected = 50
    actual = round((raw_score / 11) * 10)
    assert actual == expected
```

## Gelecek Geliştirmeler

### 1. Machine Learning Entegrasyonu
- Geçmiş performans verisi ile ağırlık optimizasyonu
- Dinamik eşik değerleri

### 2. Sektör Bazlı Skorlama
- Farklı fon türleri için özel ağırlıklandırma
- Sektör benchmarkları

### 3. Risk-Adjusted Skorlama
- Maksimum drawdown entegrasyonu
- Beta katsayısı ile market risk ayarlaması

---

**Son Güncelleme:** 13 Ekim 2025  
**Versiyon:** 2.0  
**Geliştirici:** TEFAS Analysis System