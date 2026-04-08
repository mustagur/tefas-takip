#!/usr/bin/env python3
"""
Decision Engine v2.0 - Optimize Edilmiş Karar Motoru

Yenilikler:
1. Akıllı confirm (score>=90 ise 1 gün yeter)
2. 5 günlük getiri cezası (ret_5d penalty)
3. BEKLE alt türleri (NO_TREND, LATE, CONFIRM, NO_MOMENTUM)
4. AL kotası (top 5 early + top 3 breakout)
5. trend_none için macd_bear_confirm zorunlu
6. False break simetrik (portföyde değilken de)
7. WhatsApp modu (minimal çıktı)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime


class Decision(Enum):
    """Karar türleri"""
    AL = "AL"
    ALINABILIR = "ALINABİLİR ADAY"  # Gözlemle, teyit bekle
    TUT = "TUT"
    AZALT = "AZALT"  # Pozisyonu azalt
    SAT = "SAT"      # Sat
    ALMA = "ALMA"    # Satın alma
    BEKLE = "BEKLE"


class BekleType(Enum):
    """BEKLE alt türleri"""
    NO_TREND = "Trend yok"
    LATE = "Geç faz"
    CONFIRM = "Teyit bekle"
    NO_MOMENTUM = "Momentum yok"


@dataclass
class DecisionResult:
    """Tek fon için karar sonucu"""
    fund_code: str
    decision: Decision
    reason: str
    emoji: str
    
    # Detay bilgiler (opsiyonel)
    rsi: float = 0.0
    score: int = 0
    score_final: int = 0  # Penalty uygulanmış skor
    macd_status: str = ""
    risk_level: str = ""
    strategy: str = ""
    bekle_type: Optional[BekleType] = None  # BEKLE alt türü
    al_type: str = ""  # EARLY veya BREAKOUT
    
    def to_single_line(self) -> str:
        """Tek satır format: PHE ❌ ALMA | Aşırı ısınmış"""
        return f"{self.fund_code}  {self.emoji} {self.decision.value:<5} | {self.reason}"
    
    def to_dict(self) -> Dict[str, str]:
        """JSON format"""
        return {
            "decision": self.decision.value,
            "reason": self.reason
        }
    
    def to_detail(self) -> str:
        """Detay format (tıklayınca)"""
        lines = [
            f"{self.fund_code} → {self.decision.value}",
            f"Sebep: {self.reason}",
        ]
        if self.risk_level:
            lines.append(f"Risk: {self.risk_level}")
        if self.strategy:
            lines.append(f"Strateji: {self.strategy}")
        return "\n".join(lines)


class DecisionEngine:
    """
    OPTIMIZE EDİLMİŞ Karar Motoru v2.0
    
    Özellikler:
    1. score_final = score - RSI_penalty - ret5d_penalty
    2. Akıllı MACD confirm (score>=90 → 1g yeter)
    3. AL_EARLY + AL_BREAKOUT + kota (top 5 + top 3)
    4. BEKLE alt türleri (NO_TREND, LATE, CONFIRM, NO_MOMENTUM)
    5. trend_none için macd_bear_confirm zorunlu
    6. False break simetrik koruma
    7. WhatsApp modu
    """
    
    # RSI Eşikleri
    RSI_EXTREME = 90         # Aşırı uç
    RSI_OVERHEAT = 85        # Aşırı ısınmış
    RSI_LATE = 80            # Geç faz
    RSI_MID = 68             # Orta faz
    RSI_EARLY_MAX = 68       # Erken faz üst (normal)
    RSI_BREAKOUT_MAX = 75    # Breakout AL üst sınır
    RSI_EARLY_MIN = 55       # Erken faz alt
    
    # RSI Overheat Penalty (score soğutma)
    RSI_PENALTY_EXTREME = 25  # RSI >= 90
    RSI_PENALTY_OVERHEAT = 15 # RSI 85-90
    RSI_PENALTY_LATE = 8      # RSI 80-85
    
    # 5 Günlük Getiri Cezası (şişkinlik freni)
    RET5D_PENALTY_HIGH = 18   # ret_5d >= 12%
    RET5D_PENALTY_MID = 10    # ret_5d >= 8%
    
    # Skor Eşikleri (score_final için) - 5 puan gevşetildi
    SCORE_ULTRA_STRONG = 90   # Akıllı confirm için (1g yeter)
    SCORE_STRONG_TREND = 75   # Güçlü trend (80'den 75'e)
    SCORE_TREND = 60          # Trend var (65'ten 60'a)
    SCORE_BREAKOUT = 75       # Breakout AL için minimum (80'den 75'e)
    
    # AL Kotaları
    AL_EARLY_QUOTA = 5        # Max 5 early AL
    AL_BREAKOUT_QUOTA = 3     # Max 3 breakout AL
    
    def __init__(self, overrides: dict = None):
        """
        DecisionEngine constructor
        
        Args:
            overrides: Eşik değerlerini override etmek için dict
                       Örnek: {"SCORE_TREND": 60, "SCORE_STRONG_TREND": 75}
                       Geçerli anahtarlar: SCORE_TREND, SCORE_STRONG_TREND, 
                                          SCORE_BREAKOUT, SCORE_ULTRA_STRONG,
                                          RSI_EARLY_MAX, RSI_BREAKOUT_MAX
        """
        # Override uygula
        if overrides:
            for key, value in overrides.items():
                if hasattr(self.__class__, key):
                    setattr(self, key, value)
                else:
                    print(f"⚠️ DecisionEngine: Bilinmeyen override: {key}")
        else:
            # Class değerlerini instance'a kopyala (override edilebilir olması için)
            self.SCORE_TREND = self.__class__.SCORE_TREND
            self.SCORE_STRONG_TREND = self.__class__.SCORE_STRONG_TREND
            self.SCORE_BREAKOUT = self.__class__.SCORE_BREAKOUT
            self.SCORE_ULTRA_STRONG = self.__class__.SCORE_ULTRA_STRONG
            self.RSI_EARLY_MAX = self.__class__.RSI_EARLY_MAX
            self.RSI_BREAKOUT_MAX = self.__class__.RSI_BREAKOUT_MAX
        
        self.emoji_map = {
            Decision.AL: "✅",
            Decision.ALINABILIR: "🔵",  # Mavi - gözlemde
            Decision.TUT: "🟡",
            Decision.AZALT: "⚠️",
            Decision.SAT: "🔴",
            Decision.ALMA: "❌",
            Decision.BEKLE: "⏳"
        }
    
    def analyze(self, fund_data: Dict[str, Any], is_in_portfolio: bool = False) -> DecisionResult:
        """
        OPTIMIZE EDİLMİŞ Analiz v2.0
        
        Yeni özellikler:
        1. score_final = score - RSI_penalty - ret5d_penalty
        2. Akıllı MACD confirm (score>=90 → 1g yeter)
        3. AL tipi: EARLY veya BREAKOUT
        4. BEKLE alt türleri
        5. False break simetrik koruma
        """
        fund_code = fund_data.get("fund_code", "???")
        score = fund_data.get("score", 0)
        rsi = fund_data.get("rsi", 0)
        macd = fund_data.get("macd", 0)
        macd_signal = fund_data.get("macd_signal", 0)
        stats = fund_data.get("fund_statistics", {})
        
        # 5 günlük getiri (varsa)
        ret_5d = fund_data.get("ret_5d", 0) or stats.get("pct_5d", 0) or 0
        
        # Dünkü MACD (varsa - 2 gün confirm için)
        macd_yesterday = fund_data.get("macd_yesterday", None)
        macd_signal_yesterday = fund_data.get("macd_signal_yesterday", None)
        
        # 1. SCORE_FINAL = score - RSI_penalty - ret5d_penalty
        score_final = self._calculate_score_final(score, rsi, ret_5d)
        
        # 2. MACD CONFIRM (akıllı - score>=90 ise 1g yeter)
        macd_bull = macd > macd_signal
        macd_bear = macd < macd_signal
        macd_bull_confirm, macd_bear_confirm = self._check_macd_confirm(
            macd, macd_signal, macd_yesterday, macd_signal_yesterday
        )
        
        # Akıllı confirm: score_final >= 90 ise 1 gün yeter
        smart_bull_confirm = macd_bull_confirm or (score_final >= self.SCORE_ULTRA_STRONG and macd_bull)
        
        # 3. Trend kontrolü (macd_bear_confirm zorunlu)
        has_trend = self._check_trend(score_final, rsi, macd, macd_signal, macd_bear_confirm)
        
        # 4. Faz kontrolü
        phase = self._check_phase(rsi)
        
        # 5. Risk/ödül
        risk_reward = self._check_risk_reward(stats, rsi)
        
        # 6. Karar matrisi (optimize edilmiş)
        decision, reason, risk_level, strategy, bekle_type, al_type = self._make_decision(
            has_trend, phase, risk_reward, rsi, score_final, macd, macd_signal,
            is_in_portfolio, macd_bear, smart_bull_confirm, macd_bear_confirm
        )
        
        # MACD durumu
        macd_status = "pozitif" if macd_bull else "negatif"
        if macd_bull_confirm:
            macd_status += " (2g)"
        elif smart_bull_confirm and not macd_bull_confirm:
            macd_status += " (1g-güçlü)"
        
        return DecisionResult(
            fund_code=fund_code,
            decision=decision,
            reason=reason,
            emoji=self.emoji_map[decision],
            rsi=rsi,
            score=score,  # Ham skor
            score_final=score_final,  # Penalty uygulanmış
            macd_status=macd_status,
            risk_level=risk_level,
            strategy=strategy,
            bekle_type=bekle_type,
            al_type=al_type
        )
    
    def _calculate_score_final(self, score: int, rsi: float, ret_5d: float = 0) -> int:
        """
        Score Final = Score - RSI Penalty - Ret5d Penalty
        
        1. RSI Overheat Penalty: Geç faz fonları soğut
        2. Ret5d Penalty: Son 5 günde uçmuş fonları soğut
        """
        # RSI Penalty
        rsi_penalty = 0
        if rsi >= self.RSI_EXTREME:
            rsi_penalty = self.RSI_PENALTY_EXTREME  # -25
        elif rsi >= self.RSI_OVERHEAT:
            rsi_penalty = self.RSI_PENALTY_OVERHEAT  # -15
        elif rsi >= self.RSI_LATE:
            rsi_penalty = self.RSI_PENALTY_LATE  # -8
        
        # Ret5d Penalty (şişkinlik freni)
        ret5d_penalty = 0
        if ret_5d >= 12:
            ret5d_penalty = self.RET5D_PENALTY_HIGH  # -18
        elif ret_5d >= 8:
            ret5d_penalty = self.RET5D_PENALTY_MID  # -10
        
        return max(0, score - rsi_penalty - ret5d_penalty)
    
    def _check_macd_confirm(self, macd: float, signal: float, 
                           macd_y: float, signal_y: float) -> tuple:
        """
        2 günlük MACD confirm - false break koruması
        
        Returns: (macd_bull_confirm, macd_bear_confirm)
        """
        macd_bull_today = macd > signal
        macd_bear_today = macd < signal
        
        # Dünkü veri yoksa tek gün kabul et
        if macd_y is None or signal_y is None:
            return (macd_bull_today, macd_bear_today)
        
        macd_bull_yesterday = macd_y > signal_y
        macd_bear_yesterday = macd_y < signal_y
        
        macd_bull_confirm = macd_bull_today and macd_bull_yesterday
        macd_bear_confirm = macd_bear_today and macd_bear_yesterday
        
        return (macd_bull_confirm, macd_bear_confirm)
    
    def _check_trend(self, score_final: int, rsi: float, macd: float, macd_signal: float, 
                     macd_bear_confirm: bool = False) -> str:
        """
        Trend kontrolü v2.0
        
        ÖNEMLİ: trend_none için macd_bear_confirm zorunlu!
        (1 günlük macd_bear ile trend'i öldürme)
        
        - 'strong': score_final >= 80 AND macd_bull
        - 'weak': score_final >= 65 AND macd_bull
        - 'none': (score_final < 65) OR (macd_bear_confirm)
        """
        macd_bull = macd > macd_signal
        macd_bear = macd < macd_signal
        
        # Trend kırılması için macd_bear_confirm gerekli (2 gün)
        # Tek günlük macd_bear ile trend'i öldürme!
        if macd_bear_confirm or score_final < self.SCORE_TREND:
            if not macd_bull:  # MACD pozitif değilse
                return "none"
        
        if score_final >= self.SCORE_STRONG_TREND and macd_bull:
            return "strong"
        elif score_final >= self.SCORE_TREND and macd_bull:
            return "weak"
        return "none"
    
    def _check_phase(self, rsi: float) -> str:
        """
        Faz kontrolü (güçlendirilmiş):
        - 'extreme': RSI >= 90 (SAT tetikleyici)
        - 'overheat': RSI 85-90 (ALMA tetikleyici)
        - 'late': RSI 80-85 (AZALT tetikleyici)
        - 'mid': RSI 68-80 (BEKLE - geç kaldın)
        - 'early': RSI 55-68 (AL tetikleyici)
        - 'none': RSI < 55 (sinyal yok)
        """
        if rsi >= self.RSI_EXTREME:
            return "extreme"
        elif rsi >= self.RSI_OVERHEAT:
            return "overheat"
        elif rsi >= self.RSI_LATE:
            return "late"
        elif rsi >= self.RSI_MID:
            return "mid"
        elif rsi >= self.RSI_EARLY_MIN:
            return "early"
        return "none"
    
    def _check_risk_reward(self, stats: Dict, rsi: float) -> str:
        """Risk/ödül kontrolü: 'good', 'moderate', 'poor'"""
        volatility = stats.get("volatility", 0)
        sharpe = stats.get("sharpe", 0)
        
        # Düşük volatilite + iyi Sharpe = iyi risk/ödül
        if volatility < 1.5 and sharpe > 1.0:
            return "good"
        elif volatility < 2.5 or sharpe > 0.5:
            return "moderate"
        return "poor"
    
    def _make_decision(
        self, 
        has_trend: str, 
        phase: str, 
        risk_reward: str,
        rsi: float,
        score_final: int,
        macd: float,
        macd_signal: float,
        is_in_portfolio: bool = False,
        macd_bear: bool = False,
        smart_bull_confirm: bool = False,  # Akıllı confirm (score>=90 → 1g)
        macd_bear_confirm: bool = False
    ) -> Tuple[Decision, str, str, str, Optional[BekleType], str]:
        """
        OPTIMIZE EDİLMİŞ Karar Matrisi v2.0
        
        Yeni özellikler:
        1. Akıllı confirm (score>=90 ise 1g yeter)
        2. BEKLE alt türleri
        3. False break simetrik koruma
        4. AL tipi (EARLY/BREAKOUT)
        
        Returns: (decision, reason, risk_level, strategy, bekle_type, al_type)
        """
        
        # Trend kırılması = (score_final < 65 VE macd_bear 2 gün)
        trend_broken = (score_final < self.SCORE_TREND) and macd_bear_confirm
        macd_bull = macd > macd_signal
        
        # ========== PORTFÖYDE İSE ==========
        if is_in_portfolio:
            
            # 1. Trend KİRİLDI (skor<65 VE macd_bear 2 gün) → SAT
            if trend_broken:
                return (
                    Decision.SAT,
                    "Trend kırıldı",
                    "Yüksek",
                    "Pozisyonu kapat",
                    None, ""
                )
            
            # 2. RSI >= 90 + MACD 2gün negatif → SAT
            if phase == "extreme" and macd_bear_confirm:
                return (
                    Decision.SAT,
                    "Aşırı uç + MACD 2g negatif",
                    "Yüksek",
                    "Pozisyonu kapat",
                    None, ""
                )
            
            # 3. RSI >= 90 + MACD pozitif → AZALT (trend taşıyor)
            if phase == "extreme" and macd_bull:
                return (
                    Decision.AZALT,
                    "Aşırı uç ama trend taşıyor",
                    "Yüksek",
                    "%70 kar al",
                    None, ""
                )
            
            # 4. RSI 85-90 + trend var → AZALT
            if phase == "overheat" and has_trend in ("strong", "weak"):
                return (
                    Decision.AZALT,
                    "Isınmış, trend devam",
                    "Yüksek",
                    "%50 kar al",
                    None, ""
                )
            
            # 5. RSI 85+ + trend yok + macd_bear 2g → SAT
            if phase in ("overheat", "extreme") and has_trend == "none" and macd_bear_confirm:
                return (
                    Decision.SAT,
                    "Isınmış + trend kırıldı",
                    "Yüksek",
                    "Pozisyonu kapat",
                    None, ""
                )
            
            # 6. RSI 80-85 + trend var → AZALT
            if phase == "late" and has_trend in ("strong", "weak"):
                return (
                    Decision.AZALT,
                    "Geç faz, trend devam",
                    "Orta-Yüksek",
                    "Kısmi kar al",
                    None, ""
                )
            
            # 7. Orta faz (68-80) + trend var → TUT
            if phase == "mid" and has_trend in ("strong", "weak"):
                return (
                    Decision.TUT,
                    "Orta faz, trend devam",
                    "Orta",
                    "Stop koy",
                    None, ""
                )
            
            # 8. Erken faz + trend var → TUT
            if phase == "early" and has_trend in ("strong", "weak"):
                return (
                    Decision.TUT,
                    "Erken faz, trend güçlü",
                    "Düşük",
                    "Ekleme düşün",
                    None, ""
                )
            
            # 9. Skor düştü ama MACD pozitif → TUT (dikkatli)
            if has_trend == "none" and macd_bull:
                return (
                    Decision.TUT,
                    "MACD pozitif ama skor düştü",
                    "Orta",
                    "Stop sıkılaştır",
                    None, ""
                )
            
            # 10. MACD 1g negatif ama skor güçlü → TUT (false break koruması)
            if macd_bear and not macd_bear_confirm and score_final >= self.SCORE_TREND:
                return (
                    Decision.TUT,
                    "MACD 1g negatif, skor güçlü",
                    "Orta",
                    "Panik satma",
                    None, ""
                )
            
            # Varsayılan portföy
            return (
                Decision.TUT,
                "Pozisyon koru",
                "Orta",
                "İzle",
                None, ""
            )
        
        # ========== PORTFÖYDE DEĞİLSE ==========
        
        # 1. RSI >= 85 → ALMA
        if phase in ("overheat", "extreme"):
            return (
                Decision.ALMA,
                "Aşırı ısınmış",
                "Yüksek",
                "Düzeltme bekle",
                None, ""
            )
        
        # 2. False break simetrik: macd_bear 1g + score>=65 → BEKLE_CONFIRM
        if macd_bear and not macd_bear_confirm and score_final >= self.SCORE_TREND:
            return (
                Decision.BEKLE,
                "Teyit bekle",
                "Düşük",
                "1-2 gün izle",
                BekleType.CONFIRM, ""
            )
        
        # 3. Trend yok → BEKLE_NO_TREND
        if has_trend == "none":
            return (
                Decision.BEKLE,
                "Trend yok",
                "Düşük",
                "Sinyal bekle",
                BekleType.NO_TREND, ""
            )
        
        # 4. AL_EARLY: Güçlü trend + RSI 55-68 + akıllı confirm
        if has_trend == "strong" and phase == "early" and smart_bull_confirm:
            return (
                Decision.AL,
                "Güçlü trend + erken faz",
                "Düşük",
                "Parçalı alım",
                None, "EARLY"
            )
        
        # 5. AL_BREAKOUT: Güçlü trend + RSI 68-75 + skor>=80 + akıllı confirm
        if (has_trend == "strong" and 
            rsi >= self.RSI_MID and rsi <= self.RSI_BREAKOUT_MAX and
            score_final >= self.SCORE_BREAKOUT and 
            smart_bull_confirm):
            return (
                Decision.AL,
                "Breakout girişi",
                "Düşük-Orta",
                "Momentum girişi",
                None, "BREAKOUT"
            )
        
        # 6. AL_EARLY: Zayıf trend + RSI 55-68 + akıllı confirm
        if has_trend == "weak" and phase == "early" and smart_bull_confirm:
            return (
                Decision.AL,
                "Trend başlıyor + erken faz",
                "Düşük-Orta",
                "Küçük pozisyon",
                None, "EARLY"
            )
        
        # 7. ALINABİLİR ADAY: score>=SCORE_TREND + macd_bull + confirm yok + RSI<75
        macd_bull = macd > macd_signal
        if (score_final >= self.SCORE_TREND and 
            macd_bull and 
            not smart_bull_confirm and 
            rsi < self.RSI_BREAKOUT_MAX):
            return (
                Decision.ALINABILIR,
                "Teyit bekle",
                "Düşük",
                "Yarın AL'e yükselir",
                None, ""
            )
        
        # 8. MACD confirm yok ama trend var (RSI>=75) → BEKLE
        if has_trend in ("strong", "weak") and not smart_bull_confirm:
            return (
                Decision.BEKLE,
                "Geç faz + teyit yok",
                "Orta",
                "Düzeltme bekle",
                BekleType.LATE, ""
            )
        
        # 8. Geç faz (RSI 68-80) → BEKLE_LATE
        if phase == "mid":
            return (
                Decision.BEKLE,
                "Geç faz",
                "Orta",
                "Düzeltmede al",
                BekleType.LATE, ""
            )
        
        # 9. RSI 80-85 → BEKLE_LATE
        if phase == "late":
            return (
                Decision.BEKLE,
                "Geç faz",
                "Orta-Yüksek",
                "Çok geç",
                BekleType.LATE, ""
            )
        
        # 10. RSI < 55 → BEKLE_NO_MOMENTUM
        if phase == "none":
            return (
                Decision.BEKLE,
                "Momentum yok",
                "Düşük",
                "RSI 55+ bekle",
                BekleType.NO_MOMENTUM, ""
            )
        
        # Varsayılan
        return (
            Decision.BEKLE,
            "Sinyal yok",
            "Düşük",
            "İzle",
            None, ""
        )
    
    def analyze_batch(self, funds_data: List[Dict[str, Any]], portfolio_funds: List[str] = None) -> Dict[str, DecisionResult]:
        """Toplu analiz + AL kotası uygulama
        
        Args:
            funds_data: Fon verileri listesi
            portfolio_funds: Portföydeki fon kodları (SAT/AZALT kararları için)
        """
        if portfolio_funds is None:
            portfolio_funds = []
            
        results = {}
        for fund_data in funds_data:
            fund_code = fund_data.get("fund_code", "")
            is_in_portfolio = fund_code in portfolio_funds
            result = self.analyze(fund_data, is_in_portfolio=is_in_portfolio)
            results[result.fund_code] = result
        
        # AL kotası uygula
        results = self._apply_al_quota(results, portfolio_funds)
        
        return results
    
    def _apply_al_quota(self, results: Dict[str, DecisionResult], portfolio_funds: List[str]) -> Dict[str, DecisionResult]:
        """
        AL kotası: Top N dışındakileri BEKLE_CONFIRM'e düşür
        
        - AL_EARLY: top 5
        - AL_BREAKOUT: top 3
        
        Sıralama: score_final büyük, aynıysa RSI düşük (daha erken)
        """
        # AL'ları ayır ve sırala
        al_early = []
        al_breakout = []
        
        for code, result in results.items():
            if code in portfolio_funds:
                continue  # Portföydekiler hariç
            if result.decision == Decision.AL:
                if result.al_type == "EARLY":
                    al_early.append((code, result))
                elif result.al_type == "BREAKOUT":
                    al_breakout.append((code, result))
        
        # Sırala: score_final DESC, rsi ASC
        al_early.sort(key=lambda x: (-x[1].score_final, x[1].rsi))
        al_breakout.sort(key=lambda x: (-x[1].score_final, x[1].rsi))
        
        # Kota dışındakileri BEKLE_CONFIRM'e düşür
        for i, (code, result) in enumerate(al_early):
            if i >= self.AL_EARLY_QUOTA:
                results[code] = DecisionResult(
                    fund_code=code,
                    decision=Decision.BEKLE,
                    reason="Kota dışı (sırada bekle)",
                    emoji=self.emoji_map[Decision.BEKLE],
                    rsi=result.rsi,
                    score=result.score,
                    score_final=result.score_final,
                    macd_status=result.macd_status,
                    risk_level="Düşük",
                    strategy="Sıra bekle",
                    bekle_type=BekleType.CONFIRM,
                    al_type=""
                )
        
        for i, (code, result) in enumerate(al_breakout):
            if i >= self.AL_BREAKOUT_QUOTA:
                results[code] = DecisionResult(
                    fund_code=code,
                    decision=Decision.BEKLE,
                    reason="Kota dışı (sırada bekle)",
                    emoji=self.emoji_map[Decision.BEKLE],
                    rsi=result.rsi,
                    score=result.score,
                    score_final=result.score_final,
                    macd_status=result.macd_status,
                    risk_level="Düşük-Orta",
                    strategy="Sıra bekle",
                    bekle_type=BekleType.CONFIRM,
                    al_type=""
                )
        
        return results
    
    def generate_report(self, results: Dict[str, DecisionResult], mode: str = "list", 
                         portfolio_funds: List[str] = None) -> str:
        """
        Rapor oluştur
        
        mode:
        - "list": Tek satır liste (varsayılan)
        - "whatsapp": Minimal WhatsApp modu (yeni!)
        - "json": JSON format
        - "detail": Detaylı format
        """
        if mode == "list":
            return self._generate_list_report(results)
        elif mode == "whatsapp":
            return self._generate_whatsapp_report(results, portfolio_funds or [])
        elif mode == "json":
            return self._generate_json_report(results)
        elif mode == "detail":
            return self._generate_detail_report(results)
        return ""
    
    def _generate_whatsapp_report(self, results: Dict[str, DecisionResult], portfolio_funds: List[str]) -> str:
        """
        📱 WHATSAPP MODU - Sadeleştirilmiş 3 blok
        
        1. Bugün Alınabilir  2. Yükseliş Adayları  3. Portföyüm
        """
        lines = []
        
        # Kategorilere ayır
        al_list = []
        alinabilir_list = []
        portfolio_list = []
        
        for code, result in results.items():
            is_portfolio = code in portfolio_funds
            
            if result.decision == Decision.AL:
                al_list.append((code, result))
            elif result.decision == Decision.ALINABILIR:
                alinabilir_list.append((code, result))
            elif is_portfolio and result.decision in (Decision.SAT, Decision.AZALT, Decision.TUT):
                portfolio_list.append((code, result))
        
        # Sıralama
        sort_key = lambda x: (-x[1].score_final, x[1].rsi)
        al_list.sort(key=sort_key)
        alinabilir_list.sort(key=sort_key)
        
        portfolio_priority = {Decision.SAT: 0, Decision.AZALT: 1, Decision.TUT: 2}
        portfolio_list.sort(key=lambda x: (portfolio_priority.get(x[1].decision, 9), -x[1].score_final))
        
        # BUGÜN ALINABİLİR - Top 5
        if al_list:
            lines.append("✅ BUGÜN ALINABİLİR")
            for code, result in al_list[:5]:
                type_tag = f"[{result.al_type}]" if result.al_type else ""
                lines.append(f"{code} — Bugün Alınabilir {type_tag} — {result.reason}")
            if len(al_list) > 5:
                lines.append(f"  (+{len(al_list) - 5} daha)")
            lines.append("")
        
        # YÜKSELİŞ ADAYLARI - Top 5
        if alinabilir_list:
            lines.append("📈 YÜKSELİŞ ADAYLARI")
            for code, result in alinabilir_list[:5]:
                lines.append(f"{code} — Yükseliş Adayı — {result.reason}")
            if len(alinabilir_list) > 5:
                lines.append(f"  (+{len(alinabilir_list) - 5} daha)")
            lines.append("")
        
        # PORTFÖYÜM
        if portfolio_list:
            lines.append("💼 PORTFÖYÜM")
            for code, result in portfolio_list:
                emoji = "🔴" if result.decision == Decision.SAT else \
                        "🟠" if result.decision == Decision.AZALT else "🟡"
                lines.append(f"{emoji} {code} — {result.decision.value} — {result.reason}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_list_report(self, results: Dict[str, DecisionResult]) -> str:
        """🔥 LİSTE MODU - Sadece aksiyona dönüştürülebilir kararlar"""
        lines = []
        
        # BEKLE ve ALMA filtrelenir
        priority = {
            Decision.SAT: 0, 
            Decision.AZALT: 1, 
            Decision.AL: 2, 
            Decision.ALINABILIR: 3,
            Decision.TUT: 4, 
        }
        filtered = [r for r in results.values() if r.decision not in (Decision.BEKLE, Decision.ALMA)]
        sorted_results = sorted(filtered, key=lambda x: (priority.get(x.decision, 9), -x.score_final))
        
        for result in sorted_results:
            lines.append(result.to_single_line())
        
        return "\n".join(lines)
    
    def _generate_json_report(self, results: Dict[str, DecisionResult]) -> Dict[str, Dict]:
        """JSON format"""
        return {code: result.to_dict() for code, result in results.items()}
    
    def _generate_detail_report(self, results: Dict[str, DecisionResult]) -> str:
        """Detaylı format"""
        sections = []
        for result in results.values():
            sections.append(result.to_detail())
        return "\n\n".join(sections)
    
    def generate_html_report(
        self, 
        results: Dict[str, DecisionResult],
        portfolio_funds: List[str] = None,
        title: str = "TEFAS Karar Raporu"
    ) -> str:
        """HTML formatında karar raporu oluştur - Top 5 format"""
        
        # Kategorilere ayır (3 blok: Bugün Alınabilir, Yükseliş Adayları, Portföyüm)
        al_list = []           # BUGÜN ALINABİLİR
        alinabilir_list = []   # YÜKSELİŞ ADAYLARI
        portfolio_list = []    # PORTFÖYÜM (SAT/AZALT/TUT)
        
        for code, result in results.items():
            is_portfolio = portfolio_funds and code in portfolio_funds
            item = (code, result, is_portfolio)
            
            if result.decision == Decision.AL:
                al_list.append(item)
            elif result.decision == Decision.ALINABILIR:
                alinabilir_list.append(item)
            elif is_portfolio and result.decision in (Decision.SAT, Decision.AZALT, Decision.TUT):
                portfolio_list.append(item)
            # BEKLE ve ALMA raporda gösterilmez
        
        # Sıralama
        sort_key = lambda x: (-x[1].score_final, x[1].rsi)
        al_list.sort(key=sort_key)
        alinabilir_list.sort(key=sort_key)
        
        # Portföy: SAT > AZALT > TUT öncelik sırası
        portfolio_priority = {Decision.SAT: 0, Decision.AZALT: 1, Decision.TUT: 2}
        portfolio_list.sort(key=lambda x: (portfolio_priority.get(x[1].decision, 9), -x[1].score_final))
        
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        html = f'''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        .header {{
            text-align: center;
            padding: 40px 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header .date {{ color: #888; font-size: 1.1em; }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 40px;
        }}
        .summary-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .summary-card.sat {{ border-color: #ff0000; }}
        .summary-card.azalt {{ border-color: #ff6b35; }}
        .summary-card.al {{ border-color: #00ff88; }}
        .summary-card.tut {{ border-color: #ffd700; }}
        .summary-card.bekle {{ border-color: #00d9ff; }}
        .summary-card.alma {{ border-color: #ff4757; }}
        
        .summary-number {{
            font-size: 3em;
            font-weight: 800;
            margin-bottom: 5px;
        }}
        .summary-card.sat .summary-number {{ color: #ff0000; }}
        .summary-card.azalt .summary-number {{ color: #ff6b35; }}
        .summary-card.al .summary-number {{ color: #00ff88; }}
        .summary-card.tut .summary-number {{ color: #ffd700; }}
        .summary-card.bekle .summary-number {{ color: #00d9ff; }}
        .summary-card.alma .summary-number {{ color: #ff4757; }}
        
        .summary-label {{ color: #888; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
        
        .section {{
            background: rgba(255,255,255,0.03);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .section h2 {{
            font-size: 1.5em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section.sat h2 {{ color: #ff0000; }}
        .section.azalt h2 {{ color: #ff6b35; }}
        .section.al h2 {{ color: #00ff88; }}
        .section.tut h2 {{ color: #ffd700; }}
        .section.bekle h2 {{ color: #00d9ff; }}
        .section.alma h2 {{ color: #ff4757; }}
        
        .fund-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }}
        .fund-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .fund-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .fund-card.sat {{ border-left-color: #ff0000; }}
        .fund-card.azalt {{ border-left-color: #ff6b35; }}
        .fund-card.al {{ border-left-color: #00ff88; }}
        .fund-card.tut {{ border-left-color: #ffd700; }}
        .fund-card.bekle {{ border-left-color: #00d9ff; }}
        .fund-card.alma {{ border-left-color: #ff4757; }}
        
        .fund-card.portfolio {{
            background: rgba(255,215,0,0.1);
            border: 1px solid rgba(255,215,0,0.3);
        }}
        
        .fund-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .fund-code {{
            font-size: 1.4em;
            font-weight: 700;
        }}
        .fund-card.sat .fund-code {{ color: #ff0000; }}
        .fund-card.azalt .fund-code {{ color: #ff6b35; }}
        .fund-card.al .fund-code {{ color: #00ff88; }}
        .fund-card.tut .fund-code {{ color: #ffd700; }}
        .fund-card.bekle .fund-code {{ color: #00d9ff; }}
        .fund-card.alma .fund-code {{ color: #ff4757; }}
        
        .portfolio-badge {{
            background: linear-gradient(90deg, #ffd700, #ffaa00);
            color: #000;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.7em;
            font-weight: 700;
        }}
        
        .fund-reason {{
            color: #aaa;
            font-size: 0.95em;
            margin-bottom: 10px;
        }}
        .fund-metrics {{
            display: flex;
            gap: 15px;
            font-size: 0.85em;
            color: #666;
        }}
        .metric {{ display: flex; flex-direction: column; }}
        .metric-label {{ color: #555; font-size: 0.8em; }}
        .metric-value {{ color: #fff; font-weight: 600; }}
        
        .decision-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 700;
        }}
        .decision-badge.sat {{ background: rgba(255,0,0,0.2); color: #ff0000; }}
        .decision-badge.azalt {{ background: rgba(255,107,53,0.2); color: #ff6b35; }}
        .decision-badge.al {{ background: rgba(0,255,136,0.2); color: #00ff88; }}
        .decision-badge.tut {{ background: rgba(255,215,0,0.2); color: #ffd700; }}
        .decision-badge.bekle {{ background: rgba(0,217,255,0.2); color: #00d9ff; }}
        .decision-badge.alma {{ background: rgba(255,71,87,0.2); color: #ff4757; }}
        
        .strategy {{
            margin-top: 10px;
            padding: 10px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            font-size: 0.85em;
            color: #888;
        }}
        .strategy strong {{ color: #aaa; }}
        
        .empty-message {{
            text-align: center;
            padding: 30px;
            color: #555;
            font-style: italic;
        }}
        
        @media (max-width: 768px) {{
            .summary {{ grid-template-columns: repeat(2, 1fr); }}
            .fund-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 {title}</h1>
            <div class="date">📅 {now}</div>
        </div>
        
        <div class="summary" style="grid-template-columns: repeat(3, 1fr);">
            <div class="summary-card al">
                <div class="summary-number">{len(al_list)}</div>
                <div class="summary-label">✅ Bugün Alınabilir</div>
            </div>
            <div class="summary-card" style="border-color: #3498db;">
                <div class="summary-number" style="color: #3498db;">{len(alinabilir_list)}</div>
                <div class="summary-label">📈 Yükseliş Adayları</div>
            </div>
            <div class="summary-card tut">
                <div class="summary-number">{len(portfolio_list)}</div>
                <div class="summary-label">💼 Portföyüm</div>
            </div>
        </div>
'''
        
        # BUGÜN ALINABİLİR (Top 5)
        html += self._generate_section_html("AL", "✅ Bugün Alınabilir", al_list, "al", show_all=False, max_items=5)
        
        # YÜKSELİŞ ADAYLARI (Top 5)
        html += self._generate_section_html("ALINABILIR", "📈 Yükseliş Adayları", alinabilir_list, "alinabilir", show_all=False, max_items=5)
        
        # PORTFÖYÜM (hepsi)
        html += self._generate_portfolio_section_html("💼 Portföyüm", portfolio_list)
        
        html += '''
    </div>
</body>
</html>
'''
        return html
    
    def _generate_section_html(self, decision_type: str, title: str, items: list, css_class: str, show_all: bool = True, max_items: int = 5) -> str:
        """Bölüm HTML'i oluştur - Top 5 veya hepsi"""
        if not items:
            return f'''
        <div class="section {css_class}" style="border-left: 4px solid {'#3498db' if css_class == 'alinabilir' else ''};">
            <h2>{title}</h2>
            <div class="empty-message">Bu kategoride fon bulunmuyor</div>
        </div>
'''
        
        # Top 5 veya hepsi
        display_items = items if show_all else items[:max_items]
        remaining = len(items) - len(display_items)
        
        html = f'''
        <div class="section {css_class}" style="border-left: 4px solid {'#3498db' if css_class == 'alinabilir' else ''};">
            <h2>{title}</h2>
            <div class="fund-list" style="display: flex; flex-direction: column; gap: 8px;">
'''
        
        for code, result, is_portfolio in display_items:
            portfolio_badge = ' <span style="background: #ffd700; color: #000; padding: 2px 6px; border-radius: 4px; font-size: 0.7em;">PORTFÖY</span>' if is_portfolio else ""
            
            # Basit format: KOD — KARAR — ETİKET
            html += f'''
                <div style="background: rgba(255,255,255,0.05); padding: 12px 16px; border-radius: 8px; display: flex; align-items: center; gap: 12px;">
                    <span style="font-weight: 700; font-size: 1.1em; min-width: 50px;">{code}</span>
                    <span style="color: #888;">—</span>
                    <span style="color: #aaa;">{result.reason}</span>
                    {portfolio_badge}
                </div>
'''
        
        # Kalan sayısı
        if remaining > 0:
            html += f'''
                <div style="text-align: center; padding: 10px; color: #666; font-style: italic;">
                    (+{remaining} daha)
                </div>
'''
        
        html += '''
            </div>
        </div>
'''
        return html
    
    def _generate_portfolio_section_html(self, title: str, items: list) -> str:
        """Portföy bölümü HTML'i - SAT/AZALT/TUT karışık renkli gösterim"""
        if not items:
            return f'''
        <div class="section" style="border-left: 4px solid #ffd700;">
            <h2 style="color: #ffd700;">{title}</h2>
            <div class="empty-message">Portföyde fon bulunmuyor</div>
        </div>
'''
        
        decision_styles = {
            Decision.SAT: ("#ff0000", "SAT"),
            Decision.AZALT: ("#ff6b35", "AZALT"),
            Decision.TUT: ("#ffd700", "TUT"),
        }
        
        html = f'''
        <div class="section" style="border-left: 4px solid #ffd700;">
            <h2 style="color: #ffd700;">{title}</h2>
            <div class="fund-list" style="display: flex; flex-direction: column; gap: 8px;">
'''
        
        for code, result, is_portfolio in items:
            color, label = decision_styles.get(result.decision, ("#888", "?"))
            strategy_html = f'<span style="color: #666; font-size: 0.85em;">({result.strategy})</span>' if result.strategy else ''
            html += f'''
                <div style="background: rgba(255,255,255,0.05); padding: 12px 16px; border-radius: 8px; display: flex; align-items: center; gap: 12px; border-left: 3px solid {color};">
                    <span style="font-weight: 700; font-size: 1.1em; min-width: 50px;">{code}</span>
                    <span style="background: {color}22; color: {color}; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: 700;">{label}</span>
                    <span style="color: #aaa;">{result.reason}</span>
                    {strategy_html}
                </div>
'''
        
        html += '''
            </div>
        </div>
'''
        return html


def process_json_input(json_data: List[Dict]) -> str:
    """
    JSON girişini işle ve rapor döndür
    
    Beklenen JSON formatı:
    [
        {
            "fund_code": "PHE",
            "score": 85,
            "rsi": 78.5,
            "macd": 0.0045,
            "macd_signal": 0.0032,
            "price": 1.2345,
            "fund_statistics": {
                "investor_change_7d": 5.2,
                "volume_change_7d": 12.3,
                "volatility": 1.8,
                "sharpe": 1.2,
                "pct_1d": 0.8,
                "pct_3d": 2.1,
                "pct_1w": 4.5,
                "positive_days_5": 4
            }
        },
        ...
    ]
    """
    engine = DecisionEngine()
    results = engine.analyze_batch(json_data)
    
    # Liste formatında döndür
    print("\n🔥 KARAR RAPORU")
    print("=" * 40)
    print(engine.generate_report(results, mode="list"))
    print("=" * 40)
    
    # JSON formatında da döndür
    return engine._generate_json_report(results)


# Test için örnek
if __name__ == "__main__":
    # Örnek veri
    test_data = [
        {
            "fund_code": "PHE",
            "score": 85,
            "rsi": 78.5,
            "macd": 0.0045,
            "macd_signal": 0.0032,
            "price": 1.2345
        },
        {
            "fund_code": "DAH",
            "score": 72,
            "rsi": 69.2,
            "macd": 0.0032,
            "macd_signal": 0.0028,
            "price": 0.9876
        },
        {
            "fund_code": "GAF",
            "score": 68,
            "rsi": 66.5,
            "macd": 0.0028,
            "macd_signal": 0.0030,
            "price": 1.5678
        },
        {
            "fund_code": "RDF",
            "score": 58,
            "rsi": 58.3,
            "macd": 0.0018,
            "macd_signal": 0.0015,
            "price": 0.8765
        },
        {
            "fund_code": "TLY",
            "score": 45,
            "rsi": 52.1,
            "macd": 0.0012,
            "macd_signal": 0.0015,
            "price": 1.1234
        }
    ]
    
    result = process_json_input(test_data)
    print("\n📋 JSON Çıktı:")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
