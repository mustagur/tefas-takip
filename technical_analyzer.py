#!/usr/bin/env python3
"""
Technical Analysis Module
Handles all technical analysis calculations (RSI, MACD, Bollinger Bands, scoring)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from config import config


@dataclass
class AnalysisResult:
    """Container for analysis results"""
    fund_code: str
    score: float
    decline_score: float
    criteria: List[str]
    decline_criteria: List[str]
    rsi: float
    macd: float
    macd_signal: float
    macd_yesterday: float  # Dünkü MACD (2g confirm için)
    macd_signal_yesterday: float  # Dünkü sinyal (2g confirm için)
    price: float
    signals: Dict[str, bool]
    has_recent_momentum: bool = False  # New field for momentum filter


@dataclass
class CandidateResult:
    """Container for candidate fund results"""
    fund_code: str
    score: float
    criteria: str
    rsi: float
    macd: float
    macd_signal: float
    price: float
    fund_statistics: Dict[str, Any]
    company: str = 'Bilinmeyen'  # Add company field


class TechnicalAnalyzer:
    """Handles all technical analysis calculations and scoring"""
    
    def __init__(self):
        self.config = config.technical
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        if df.empty or len(df) < max(self.config.rsi_period, self.config.bollinger_period):
            return df
        
        df = df.copy()
        close = df["price"]
        
        # Bollinger Bands
        df = self._calculate_bollinger_bands(df, close)
        
        # RSI
        df = self._calculate_rsi(df, close)
        
        # MACD
        df = self._calculate_macd(df, close)
        
        return df
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, close: pd.Series) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        ma = close.rolling(self.config.bollinger_period).mean()
        std = close.rolling(self.config.bollinger_period).std()
        df["bb_upper"] = ma + (self.config.bollinger_std * std)
        df["bb_lower"] = ma - (self.config.bollinger_std * std)
        df["bb_middle"] = ma
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, close: pd.Series) -> pd.DataFrame:
        """Calculate RSI"""
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.rolling(self.config.rsi_period).mean()
        avg_loss = loss.rolling(self.config.rsi_period).mean()
        
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))
        return df
    
    def _calculate_macd(self, df: pd.DataFrame, close: pd.Series) -> pd.DataFrame:
        """Calculate MACD"""
        ema_fast = close.ewm(span=self.config.macd_fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.config.macd_slow, adjust=False).mean()
        
        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=self.config.macd_signal, adjust=False).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]
        return df
    
    def analyze_fund(self, df: pd.DataFrame, fund_code: str) -> AnalysisResult:
        """
        Perform comprehensive technical analysis with new 100-point scoring system
        Returns analysis result with enhanced scores and detailed criteria
        """
        if df.empty or len(df) < 2:
            return self._empty_result(fund_code)
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        if len(df) < 2:
            return self._empty_result(fund_code)
        
        # Calculate comprehensive score using new 100-point system
        comprehensive_score, comprehensive_criteria = self.calculate_comprehensive_score(df, fund_code)
        
        # Check recent momentum
        has_momentum = self._check_recent_momentum(df)
        
        # Get current and previous values for legacy signals
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Calculate legacy signals for decline analysis
        signals = self._calculate_signals(current, previous)
        decline_score = self._calculate_decline_score(signals)
        decline_criteria = self._build_criteria(signals, is_upward=False)
        
        # Dünkü MACD değerleri (2 gün confirm için)
        macd_yesterday = round(previous["macd"], 4) if pd.notna(previous["macd"]) else None
        macd_signal_yesterday = round(previous["macd_signal"], 4) if pd.notna(previous["macd_signal"]) else None
        
        return AnalysisResult(
            fund_code=fund_code,
            score=comprehensive_score,
            decline_score=decline_score,
            criteria=comprehensive_criteria,
            decline_criteria=decline_criteria,
            rsi=round(current["rsi"], 1) if pd.notna(current["rsi"]) else 0.0,
            macd=round(current["macd"], 4) if pd.notna(current["macd"]) else 0.0,
            macd_signal=round(current["macd_signal"], 4) if pd.notna(current["macd_signal"]) else 0.0,
            macd_yesterday=macd_yesterday,
            macd_signal_yesterday=macd_signal_yesterday,
            price=round(current["price"], 4),
            signals=signals,
            has_recent_momentum=has_momentum
        )
    
    def _empty_result(self, fund_code: str) -> AnalysisResult:
        """Return empty analysis result"""
        return AnalysisResult(
            fund_code=fund_code,
            score=0.0,
            decline_score=0.0,
            criteria=[],
            decline_criteria=[],
            rsi=0.0,
            macd=0.0,
            macd_signal=0.0,
            macd_yesterday=None,
            macd_signal_yesterday=None,
            price=0.0,
            signals={},
            has_recent_momentum=False
        )
    
    def _calculate_signals(self, current: pd.Series, previous: pd.Series) -> Dict[str, bool]:
        """Calculate all trading signals"""
        signals = {}
        
        # Bollinger Bands signals
        signals['bb_breakout'] = current["price"] > current["bb_upper"]
        signals['bb_breakdown'] = current["price"] < current["bb_lower"]
        signals['bb_break_down'] = current["price"] < current["bb_upper"] * 0.98
        
        # MACD signals
        signals['macd_cross_up'] = (current["macd"] > current["macd_signal"] and 
                                   previous["macd"] <= previous["macd_signal"])
        signals['macd_cross_down'] = (current["macd"] < current["macd_signal"] and 
                                     previous["macd"] >= previous["macd_signal"])
        
        # RSI signals
        signals['rsi_early_momentum'] = (self.config.rsi_early_min <= current["rsi"] < self.config.rsi_early_max and 
                                       previous["rsi"] < self.config.rsi_early_min)
        signals['rsi_strong_trend'] = (current["rsi"] >= self.config.rsi_strong_min and 
                                     previous["rsi"] < self.config.rsi_strong_min)
        signals['rsi_fall'] = (current["rsi"] <= self.config.rsi_decline_max and 
                              previous["rsi"] > self.config.rsi_decline_max)
        
        return signals
    
    def _calculate_upward_score(self, signals: Dict[str, bool]) -> float:
        """Calculate comprehensive upward momentum score (100-point system)"""
        score = 0.0
        
        # Trend Component (Max 40 points)
        if signals.get('macd_cross_up', False):
            score += self.config.macd_score  # 20 points
        
        if signals.get('bb_breakout', False):
            score += self.config.bollinger_score  # 10 points
        
        if signals.get('rsi_strong_trend', False):
            score += self.config.rsi_strong_score  # 10 points
        
        return score
    
    def calculate_comprehensive_score(self, df: pd.DataFrame, fund_code: str) -> Tuple[float, List[str]]:
        """Calculate comprehensive 100-point score with all components"""
        if df.empty or len(df) < 20:
            return 0.0, []
        
        score_raw = 0.0
        criteria = []
        
        # 1. Trend Component (Max 40 points)
        trend_score, trend_criteria = self._calculate_trend_component(df)
        score_raw += trend_score
        criteria.extend(trend_criteria)
        
        # 2. Investor Flow Component (Max 20 points)
        investor_score, investor_criteria = self._calculate_investor_flow_component(df)
        score_raw += investor_score
        criteria.extend(investor_criteria)
        
        # 3. Volume & Liquidity Component (Max 20 points)
        volume_score, volume_criteria = self._calculate_volume_liquidity_component(df)
        score_raw += volume_score
        criteria.extend(volume_criteria)
        
        # 4. Volatility Component (Max 20 points)
        volatility_score, volatility_criteria = self._calculate_volatility_component(df)
        score_raw += volatility_score
        criteria.extend(volatility_criteria)
        
        # 5. Timing Component (Max 10 points)
        timing_score, timing_criteria = self._calculate_timing_component(df)
        score_raw += timing_score
        criteria.extend(timing_criteria)
        
        # Normalize from 110-point scale to 100-point scale
        final_score = round((score_raw / 11) * 10)
        
        return final_score, criteria
    
    def _calculate_trend_component(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """Calculate Trend Component (RSI, MACD, Bollinger) - Max 40 points"""
        score = 0
        criteria = []
        
        if len(df) < 2:
            return score, criteria
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # RSI > 60 (+10 points)
        if pd.notna(current.get('rsi', 0)) and current['rsi'] > self.config.rsi_strong_min:
            score += self.config.rsi_strong_score
            criteria.append(f"RSI Güçlü ({current['rsi']:.1f}) (+{self.config.rsi_strong_score})")
        
        # MACD positive crossover (+20 points)
        if (pd.notna(current.get('macd', 0)) and pd.notna(current.get('macd_signal', 0)) and
            pd.notna(previous.get('macd', 0)) and pd.notna(previous.get('macd_signal', 0))):
            if current['macd'] > current['macd_signal'] and previous['macd'] <= previous['macd_signal']:
                score += self.config.macd_score
                criteria.append(f"MACD Pozitif Kesişim (+{self.config.macd_score})")
        
        # Bollinger breakout (+10 points)
        if (pd.notna(current.get('price', 0)) and pd.notna(current.get('bb_upper', 0)) and
            current['price'] > current['bb_upper']):
            score += self.config.bollinger_score
            criteria.append(f"Bollinger Kırılım (+{self.config.bollinger_score})")
        
        return score, criteria
    
    def _calculate_investor_flow_component(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """Calculate Investor Flow Component - Max 20 points"""
        score = 0
        criteria = []
        
        if len(df) < 7:
            return score, criteria
        
        current = df.iloc[-1]
        week_ago = df.iloc[-7]
        
        # Check 7-day investor growth >3% and AUM increase
        current_investors = current.get('number_of_investors', 0) or 0
        week_investors = week_ago.get('number_of_investors', 0) or 0
        current_aum = current.get('market_cap', 0) or 0
        week_aum = week_ago.get('market_cap', 0) or 0
        
        if week_investors > 0:
            investor_growth = ((current_investors - week_investors) / week_investors) * 100
            if investor_growth > 3 and current_aum > week_aum:
                score += self.config.investor_flow_score
                criteria.append(f"Yatırımcı Akımı ({investor_growth:.1f}% artış) (+{self.config.investor_flow_score})")
        
        return score, criteria
    
    def _calculate_volume_liquidity_component(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """Calculate Volume & Liquidity Component - Max 20 points"""
        score = 0
        criteria = []
        
        if len(df) < 6:
            return score, criteria
        
        # Get recent volume data
        recent_volumes = df.tail(6)['market_cap'].dropna()
        if len(recent_volumes) < 6:
            return score, criteria
        
        # Check daily volume increase and 5-day average rising
        latest_volume = recent_volumes.iloc[-1]
        previous_volume = recent_volumes.iloc[-2]
        five_day_avg_recent = recent_volumes.tail(5).mean()
        five_day_avg_older = recent_volumes.head(5).mean()
        
        if latest_volume > previous_volume and five_day_avg_recent > five_day_avg_older:
            volume_increase = ((latest_volume - previous_volume) / previous_volume) * 100
            avg_increase = ((five_day_avg_recent - five_day_avg_older) / five_day_avg_older) * 100
            score += self.config.volume_liquidity_score
            criteria.append(f"Hacim Artışı (Günlük: {volume_increase:.1f}%, 5G Ort: {avg_increase:.1f}%) (+{self.config.volume_liquidity_score})")
        
        return score, criteria
    
    def _calculate_volatility_component(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """Calculate Volatility Component - Max 20 points"""
        score = 0
        criteria = []
        
        if len(df) < 20:
            return score, criteria
        
        # Calculate Average True Range (ATR) and Sharpe-like ratio
        recent_returns = df.tail(20)['pct'].dropna()
        if len(recent_returns) < 10:
            return score, criteria
        
        # ATR approximation using price volatility
        volatility = recent_returns.std()
        avg_return = recent_returns.mean()
        
        # Simple Sharpe-like ratio (return/volatility)
        if volatility > 0:
            sharpe_like = avg_return / volatility
            if volatility < 2.0 and sharpe_like > 1.0:  # Low volatility and good risk-adjusted return
                score += self.config.volatility_score
                criteria.append(f"Düşük Volatilite (Vol: {volatility:.2f}, Sharpe: {sharpe_like:.2f}) (+{self.config.volatility_score})")
        
        return score, criteria
    
    def _calculate_timing_component(self, df: pd.DataFrame) -> Tuple[int, List[str]]:
        """Calculate Timing Component - Max 10 points"""
        score = 0
        criteria = []
        
        if len(df) < 5:
            return score, criteria
        
        # Check last 5 days for 4+ positive closes
        recent_changes = df.tail(5)['pct'].dropna()
        if len(recent_changes) == 5:
            positive_days = (recent_changes > 0).sum()
            if positive_days >= 4:
                score += self.config.timing_score
                criteria.append(f"Güçlü Zamanlama ({positive_days}/5 pozitif gün) (+{self.config.timing_score})")
        
        return score, criteria
    
    def _calculate_decline_score(self, signals: Dict[str, bool]) -> float:
        """Calculate decline momentum score"""
        score = 0.0
        
        if signals.get('macd_cross_down', False):
            score += self.config.macd_score
        
        if signals.get('bb_breakdown', False):
            score += self.config.bollinger_score
        
        if signals.get('rsi_fall', False):
            score += self.config.rsi_strong_score
        
        return score
    
    def analysis_to_candidate(self, analysis: AnalysisResult) -> CandidateResult:
        """Convert AnalysisResult to CandidateResult"""
        criteria_str = ", ".join(analysis.criteria) if analysis.criteria else "Belirgin trend sinyali yok"
        
        return CandidateResult(
            fund_code=analysis.fund_code,
            score=analysis.score,
            criteria=criteria_str,
            rsi=analysis.rsi,
            macd=analysis.macd,
            macd_signal=analysis.macd_signal,
            price=analysis.price,
            fund_statistics={}
        )
    
    def _build_criteria(self, signals: Dict[str, bool], is_upward: bool = True) -> List[str]:
        """Build criteria description list"""
        criteria = []
        
        if is_upward:
            if signals.get('macd_cross_up', False):
                criteria.append(f"MACD Pozitif Kesişim (+{self.config.macd_score})")
            if signals.get('bb_breakout', False):
                criteria.append(f"Bollinger Kırılım (+{self.config.bollinger_score})")
            if signals.get('rsi_early_momentum', False):
                criteria.append(f"RSI Erken Momentum {self.config.rsi_early_min}-{self.config.rsi_early_max} (+{self.config.rsi_early_score})")
            if signals.get('rsi_strong_trend', False):
                criteria.append(f"RSI Güçlü Trend {self.config.rsi_strong_min}+ (+{self.config.rsi_strong_score})")
        else:
            if signals.get('macd_cross_down', False):
                criteria.append(f"MACD Negatif Kesişim (+{self.config.macd_score})")
            if signals.get('bb_break_down', False):
                criteria.append(f"Bollinger Düşüm (+{self.config.bollinger_score})")
            if signals.get('rsi_fall', False):
                criteria.append(f"RSI Düşüm (+{self.config.rsi_strong_score})")
        
        return criteria
    
    def _check_recent_momentum(self, df: pd.DataFrame) -> bool:
        """Check if fund has recent positive momentum (2+ positive days in last 3 OR avg 3-day change > 0.5%)"""
        if df.empty or len(df) < 3:
            return False
        
        # Get last 3 days of percentage changes
        recent_changes = df.tail(3)['pct'].dropna()
        if len(recent_changes) < 3:
            return False
        
        # Check condition 1: At least 2 positive days in last 3
        positive_days = (recent_changes > 0).sum()
        if positive_days >= 2:
            return True
        
        # Check condition 2: Average 3-day change > 0.5%
        avg_change = recent_changes.mean()
        if avg_change > 0.5:
            return True
        
        return False
    
    def categorize_candidates(self, results: List[AnalysisResult], fund_statistics: Dict[str, Dict], fund_companies: Dict[str, str] = None) -> Tuple[List[CandidateResult], List[CandidateResult]]:
        """
        Categorize analysis results into early momentum and trend candidates
        Applies user rules for score adjustment and momentum filters
        """
        early_momentum = []
        trend_candidates = []
        
        if fund_companies is None:
            fund_companies = {}
        
        for result in results:
            if result.score >= config.analysis.early_momentum_min_score:
                # Apply momentum filter: must have recent positive momentum
                if not result.has_recent_momentum:
                    continue
                
                fund_stats = fund_statistics.get(result.fund_code, {})
                company = fund_companies.get(result.fund_code, 'Bilinmeyen')
                
                candidate = CandidateResult(
                    fund_code=result.fund_code,
                    score=result.score,
                    criteria=", ".join(result.criteria),
                    rsi=result.rsi,
                    macd=result.macd,
                    macd_signal=result.macd_signal,
                    price=result.price,
                    fund_statistics=fund_stats,
                    company=company
                )
                
                if config.analysis.early_momentum_min_score <= result.score < config.analysis.trend_min_score:
                    # Apply user rule: update RSI to 55-60 range and set score to 2
                    candidate.rsi = min(60, max(55, candidate.rsi))
                    candidate.score = 2.0
                    early_momentum.append(candidate)
                elif result.score >= config.analysis.trend_min_score:
                    # Keep current RSI value and score for trend candidates
                    trend_candidates.append(candidate)
        
        return early_momentum, trend_candidates
    
    def analyze_case_patterns(self, df: pd.DataFrame, fund_code: str) -> Dict[str, Any]:
        """Analyze case patterns (consecutive gains, cumulative gains)"""
        if df.empty or len(df) < max(config.analysis.case1_streak_days, config.analysis.case2_window_days, config.analysis.case3_window_days):
            return {}
        
        results = {}
        
        # Case 1: Consecutive daily gains
        case1_window = df.tail(config.analysis.case1_streak_days)
        if (case1_window["pct"].dropna() >= config.analysis.case1_min_daily).all():
            results["case1"] = {
                "fund": fund_code,
                "dates": [str(d)[:10] for d in case1_window["date"]],
                "daily_pct": [round(x, 2) if pd.notna(x) else None for x in case1_window["pct"]],
                "cumulative_pct": round(self._safe_cumulative_pct(case1_window["pct"]), 2)
            }
        
        # Case 2: Short-term cumulative gain
        case2_window = df.tail(config.analysis.case2_window_days)
        case2_total = self._safe_cumulative_pct(case2_window["pct"])
        if case2_total >= config.analysis.case2_min_cum:
            results["case2"] = {
                "fund": fund_code,
                "dates": [str(d)[:10] for d in case2_window["date"]],
                "daily_pct": [round(x, 2) if pd.notna(x) else None for x in case2_window["pct"]],
                "cumulative_pct": round(case2_total, 2)
            }
        
        # Case 3: Weekly cumulative gain
        case3_window = df.tail(config.analysis.case3_window_days)
        case3_total = self._safe_cumulative_pct(case3_window["pct"])
        if case3_total >= config.analysis.case3_min_cum:
            results["case3"] = {
                "fund": fund_code,
                "dates": [str(d)[:10] for d in case3_window["date"]],
                "daily_pct": [round(x, 2) if pd.notna(x) else None for x in case3_window["pct"]],
                "cumulative_pct": round(case3_total, 2)
            }
        
        return results
    
    def _safe_cumulative_pct(self, pct_series: pd.Series) -> float:
        """Safely calculate cumulative percentage"""
        try:
            clean_pct = pct_series.dropna()
            if clean_pct.empty:
                return 0.0
            return ((1 + clean_pct / 100.0).prod() - 1) * 100.0
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0
    
    def determine_trend_status(self, result: AnalysisResult) -> Tuple[str, str]:
        """Determine trend status and description"""
        if result.score >= config.analysis.trend_min_score:
            return "🔥 Güçlü Yükseliş", ", ".join(result.criteria)
        elif result.score >= config.analysis.early_momentum_min_score:
            return "📈 Yükseliş Sinyali", ", ".join(result.criteria)
        elif result.decline_score >= config.analysis.trend_min_score:
            return "🔴 Güçlü Düşüş", ", ".join(result.decline_criteria)
        elif result.decline_score >= config.analysis.early_momentum_min_score:
            return "📉 Düşüş Sinyali", ", ".join(result.decline_criteria)
        else:
            return "➡️ Durağan/Kararsız", "Belirgin trend sinyali yok"


if __name__ == "__main__":
    # Test technical analyzer
    analyzer = TechnicalAnalyzer()
    
    # Create sample data for testing
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    prices = np.cumsum(np.random.randn(50) * 0.02) + 100
    
    test_df = pd.DataFrame({
        'date': dates,
        'price': prices
    })
    test_df["pct"] = test_df["price"].pct_change() * 100.0
    
    # Test analysis
    result = analyzer.analyze_fund(test_df, "TEST")
    print(f"Analysis result: Score={result.score}, RSI={result.rsi}, MACD={result.macd}")
    
    # Test case patterns
    case_results = analyzer.analyze_case_patterns(test_df, "TEST")
    print(f"Case patterns: {list(case_results.keys())}")