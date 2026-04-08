# 🔥 TEFAS Karar Motoru Dokümantasyonu

## Genel Bakış

Bu karar motoru, TEFAS fonları için AL/TUT/SAT/AZALT/BEKLE/ALMA sinyalleri üretir.
Temel prensipler:
- Daha az yanlış alarm
- Daha erken yakalama  
- Daha az şişmiş fon önerisi

---

## 📊 Değişkenler

| Değişken | Hesaplama | Açıklama |
|----------|-----------|----------|
| `score` | 100 puan sistemi | Ham trend skoru (MACD + Bollinger + Yatırımcı + Hacim + Zamanlama) |
| `score_final` | `score - RSI_penalty` | RSI penalty uygulanmış soğutulmuş skor |
| `rsi` | RSI(14) | Momentum göstergesi (0-100) |
| `macd_bull` | `macd > signal` | Bugün MACD pozitif mi? |
| `macd_bull_confirm` | 2 gün üst üste pozitif | Teyitli pozitif (false break koruması) |
| `macd_bear_confirm` | 2 gün üst üste negatif | Teyitli negatif (SAT için gerekli) |

---

## 🧊 RSI Penalty (Skor Soğutma)

Geç faz fonların "top aday" listesine çıkmasını engeller.

```
RSI >= 90  →  penalty = 25
RSI 85-90  →  penalty = 15
RSI 80-85  →  penalty = 8
RSI < 80   →  penalty = 0

score_final = max(0, score - penalty)
```

**Örnek:** Skor 80, RSI 92 → score_final = 80 - 25 = 55 (trend yok kategorisine düşer)

---

## 📈 Trend Tanımı

```
trend = (score_final >= 65) AND (macd_bull)
```

| Trend Türü | Koşul |
|------------|-------|
| **Güçlü (strong)** | score_final >= 80 AND macd_bull |
| **Zayıf (weak)** | score_final 65-80 AND macd_bull |
| **Yok (none)** | score_final < 65 VEYA macd_bear |

---

## 🚨 Trend Kırılması

```
trend_broken = (score_final < 65) AND (macd_bear_confirm)
```

**ÖNEMLİ:** Tek günlük macd_bear = SAT DEĞİL!
- MACD 1 gün negatife dönebilir (false break)
- Score hâlâ yüksekse → panik satma, izle
- SAT için hem skor düşmeli HEM DE MACD 2 gün negatif olmalı

---

## 📉 RSI Fazları

```
RSI   0────55────68────75────80────85────90────100
         │      │      │      │      │      │
        none  early   mid  breakout late overheat extreme
```

| Faz | RSI Aralığı | Anlamı |
|-----|-------------|--------|
| `none` | < 55 | Henüz momentum yok |
| `early` | 55-68 | **AL_EARLY bölgesi** - ideal giriş noktası |
| `mid` | 68-75 | **AL_BREAKOUT bölgesi** (sadece güçlü trend için) |
| `late` | 75-80 | Geç faz - yeni giriş riskli |
| `overheat` | 80-85 | AZALT bölgesi (portföydeyse) |
| `extreme` | 85-90 | ALMA bölgesi (yeni giriş) / Ağır AZALT (portföydeyse) |
| `critical` | >= 90 | Kritik bölge - SAT veya ağır AZALT |

---

## 🎯 KARARLAR

### 🔴 SAT (Hemen Sat)

**Koşul:** Portföyde VE aşağıdakilerden biri:

1. `trend_broken` = skor < 65 + macd_bear 2 gün üst üste
2. RSI >= 90 + macd_bear 2 gün üst üste
3. RSI >= 85 + trend yok + macd_bear 2 gün üst üste

**Strateji:** Pozisyonu kapat

**Neden 2 gün şartı?** Tek günlük MACD değişimi gürültü olabilir. 2 gün üst üste negatif = gerçek trend kırılması.

---

### ⚠️ AZALT (Kısmi Kar Al)

**Koşul:** Portföyde VE aşağıdakilerden biri:

1. RSI >= 90 + macd_bull → **%70 kar al, %30 taşı**
2. RSI 85-90 + trend var → **%50 kar al**
3. RSI 80-85 + trend var → **Kısmi kar al, stop sıkılaştır**

**Strateji:** Kar kilitle ama trend taşımaya devam et

**Neden tam satmıyoruz?** RSI 90+ güçlü trendlerde 1-2 hafta kalabilir. MACD hâlâ pozitifse trend devam ediyor demektir.

---

### 🟡 TUT (Pozisyon Koru)

**Koşul:** Portföyde VE aşağıdakilerden biri:

1. RSI 68-80 + trend var → Pozisyon koru, stop koy
2. RSI 55-68 + trend var → Pozisyon koru, ekleme düşün
3. macd_bear 1 gün + skor >= 65 → **False break koruması, panik satma**
4. skor < 65 + macd_bull → Trend zayıflıyor ama henüz kırılmadı

**Strateji:** Pozisyon koru, stop sıkılaştır

**False break koruması:** MACD 1 gün negatife döndü ama skor hâlâ güçlü? Bu muhtemelen geçici bir düşüş. 1-2 gün bekle.

---

### ✅ AL (Satın Al)

**Koşul:** Portföyde değil VE aşağıdakilerden biri:

#### AL_EARLY (İdeal Giriş)
- RSI 55-68 (erken faz)
- Trend var (skor >= 65)
- macd_bull_confirm (2 gün pozitif)

**Strateji:** Parçalı alım

#### AL_BREAKOUT (Breakout Girişi)
- RSI 68-75 (mid faz)
- Güçlü trend (skor >= 80)
- macd_bull_confirm (2 gün pozitif)

**Strateji:** Breakout girişi, biraz daha riskli ama güçlü trendlerde fırsat

**Neden MACD confirm?** Tek günlük sinyal gürültü olabilir. 2 gün üst üste pozitif = gerçek trend başlangıcı.

---

### ⏳ BEKLE (Sinyal Bekle)

**Koşul:** Portföyde değil VE aşağıdakilerden biri:

1. **"Trend yok"** → skor < 65 veya macd_bear
2. **"Geç faz"** → RSI 75-85 (düzeltme bekle)
3. **"MACD teyitsiz"** → trend var ama macd_bull_confirm yok (1-2 gün bekle)
4. **"RSI düşük"** → RSI < 55 (henüz momentum yok)

**Strateji:** Sinyal bekle veya düzeltmede giriş yap

---

### ❌ ALMA (Satın Alma)

**Koşul:** Portföyde değil VE RSI >= 85

**Strateji:** Düzeltme bekle, acele etme

**Neden?** RSI 85+ = aşırı ısınmış. Düzeltme olasılığı yüksek. Yeni giriş için uygun değil.

---

## 📋 Karar Akış Şeması

```
                         FON ANALİZİ
                              │
                  ┌───────────┴───────────┐
                  │     PORTFÖYDE Mİ?     │
                  └───────────┬───────────┘
                         │         │
                       EVET      HAYIR
                         │         │
         ┌───────────────┘         └───────────────┐
         │                                         │
         ▼                                         ▼
┌─────────────────┐                     ┌─────────────────┐
│ skor<65 +       │                     │   RSI >= 85?    │
│ macd_bear 2g?   │                     └────────┬────────┘
└────────┬────────┘                              │
         │                                  EVET │ HAYIR
    EVET │ HAYIR                                 │    │
         │    │                                  ▼    │
         ▼    │                               ALMA   │
       SAT    │                                      │
              │                          ┌───────────┘
         ┌────┘                          │
         │                               ▼
         ▼                      ┌─────────────────┐
┌─────────────────┐             │   Trend var?    │
│ RSI>=90 +       │             │ (skor>=65 +     │
│ macd_bull?      │             │  macd_bull)     │
└────────┬────────┘             └────────┬────────┘
         │                               │
    EVET │ HAYIR                    EVET │ HAYIR
         │    │                          │    │
         ▼    │                          │    ▼
      AZALT   │                          │  BEKLE
      (%70)   │                          │  "Trend yok"
              │                          │
         ┌────┘                 ┌────────┘
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ RSI 80-90 +     │    │ macd_bull       │
│ trend var?      │    │ confirm (2g)?   │
└────────┬────────┘    └────────┬────────┘
         │                      │
    EVET │ HAYIR           EVET │ HAYIR
         │    │                 │    │
         ▼    │                 │    ▼
      AZALT   │                 │  BEKLE
              │                 │  "Teyit bekle"
         ┌────┘                 │
         │              ┌───────┘
         ▼              │
┌─────────────────┐     ▼
│ macd_bear 1g +  │  ┌─────────────────┐
│ skor>=65?       │  │ RSI 55-68?      │
└────────┬────────┘  │ (early faz)     │
         │           └────────┬────────┘
    EVET │ HAYIR              │
         │    │          EVET │ HAYIR
         ▼    │               │    │
       TUT    │               ▼    │
    "False    │            AL_EARLY│
     break"   │                    │
              │           ┌────────┘
         ┌────┘           │
         │                ▼
         ▼       ┌─────────────────┐
       TUT       │ RSI 68-75 +     │
                 │ skor>=80?       │
                 └────────┬────────┘
                          │
                     EVET │ HAYIR
                          │    │
                          ▼    ▼
                    AL_BREAKOUT  BEKLE
                                "Geç faz"
```

---

## 🆚 Özet Karar Tablosu

| Durum | Portföyde | Portföyde Değil |
|-------|-----------|-----------------|
| **skor<65 + macd_bear 2g** | 🔴 SAT | ⏳ BEKLE |
| **RSI ≥90 + macd_bear 2g** | 🔴 SAT | ❌ ALMA |
| **RSI ≥90 + macd_bull** | ⚠️ AZALT %70 | ❌ ALMA |
| **RSI 85-90 + trend** | ⚠️ AZALT %50 | ❌ ALMA |
| **RSI 80-85 + trend** | ⚠️ AZALT | ⏳ BEKLE |
| **RSI 68-80 + trend** | 🟡 TUT | ⏳ BEKLE (geç faz) |
| **RSI 68-75 + skor≥80 + confirm** | 🟡 TUT | ✅ AL_BREAKOUT |
| **RSI 55-68 + trend + confirm** | 🟡 TUT | ✅ AL_EARLY |
| **RSI 55-68 + trend + NO confirm** | 🟡 TUT | ⏳ BEKLE (teyit bekle) |
| **macd_bear 1g + skor≥65** | 🟡 TUT (false break) | ⏳ BEKLE |
| **RSI < 55 + trend** | 🟡 TUT | ⏳ BEKLE (RSI bekle) |
| **Trend yok** | 🟡 TUT / 🔴 SAT | ⏳ BEKLE |

---

## 🎯 Eşik Değerleri

### RSI Eşikleri
```
RSI_EXTREME = 90       # Aşırı uç
RSI_OVERHEAT = 85      # Aşırı ısınmış
RSI_LATE = 80          # Geç faz
RSI_MID = 68           # Orta faz
RSI_BREAKOUT_MAX = 75  # Breakout AL üst sınır
RSI_EARLY_MIN = 55     # Erken faz alt sınır
```

### RSI Penalty (Skor Soğutma)
```
RSI >= 90  →  -25 puan
RSI 85-90  →  -15 puan
RSI 80-85  →  -8 puan
```

### Skor Eşikleri
```
SCORE_STRONG_TREND = 80   # Güçlü trend (AL_BREAKOUT için)
SCORE_TREND = 65          # Normal trend
SCORE_BREAKOUT = 80       # Breakout AL için minimum
```

---

## 📈 Kazanımlar

Bu sistem şunları sağlar:

✔ **Zirvede full satmaz** - RSI 90+ ama MACD pozitifse AZALT (SAT değil)
✔ **Trend bozulmadan satmaz** - SAT için 2 gün macd_bear + skor düşüşü gerekli
✔ **Geç fazda yeni aldırmaz** - RSI 75+ = BEKLE veya ALMA
✔ **Erken fazı yakalar** - RSI 55-68 = AL_EARLY
✔ **Breakout'ları kaçırmaz** - RSI 68-75 + güçlü trend = AL_BREAKOUT
✔ **False break'te panik satmaz** - 1 günlük MACD negatif = TUT (bekle)

---

## 🔧 Kullanım

```bash
# Karar raporu oluştur
python3 run_decision_report.py --full

# HTML rapor otomatik oluşturulur: karar_raporu.html
```

---

## 📝 Versiyon Geçmişi

- **v1.0** - Temel karar motoru (AL/TUT/SAT/BEKLE/ALMA)
- **v2.0** - SAT/AZALT ayrımı, RSI fazları
- **v3.0** - RSI penalty, MACD 2g confirm, AL_BREAKOUT, false break koruması
