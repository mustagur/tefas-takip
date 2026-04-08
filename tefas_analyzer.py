#!/usr/bin/env python3
"""
TEFAS Analyzer - Main Orchestrator Class
Coordinates all analysis components and manages the complete workflow
"""

import time
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Tuple

from config import config
from data_provider import FundDataProvider
from technical_analyzer import TechnicalAnalyzer, AnalysisResult, CandidateResult
from panel_manager import PanelManager

logger = logging.getLogger(__name__)


class AnalysisStats:
    """Container for analysis statistics"""
    def __init__(self):
        self.total_funds = 0
        self.processed_funds = 0
        self.filtered_out = 0
        self.early_momentum_count = 0
        self.trend_candidates_count = 0
        self.portfolio_alerts = 0
        self.start_time = time.time()
        
    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time
    
    @property
    def processing_rate(self) -> float:
        return self.processed_funds / self.elapsed_time if self.elapsed_time > 0 else 0


class TefasAnalyzer:
    """
    Main analyzer class that orchestrates the entire TEFAS analysis process
    """
    
    def __init__(self):
        self.config = config
        self.data_provider = FundDataProvider()
        self.technical_analyzer = TechnicalAnalyzer()
        self.panel_manager = PanelManager()
        self.stats = AnalysisStats()
        
        # Analysis results storage
        self.analysis_results: List[AnalysisResult] = []
        self.portfolio_analysis: List[Dict[str, Any]] = []
        self.case_results = {"case1": [], "case2": [], "case3": []}
        self.declining_funds: List[Dict[str, Any]] = []
        self.fund_companies: Dict[str, str] = {}  # Store company info during analysis
        
    def run_analysis(self) -> Dict[str, Any]:
        """
        Run complete TEFAS analysis workflow
        Returns summary of analysis results
        """
        print("🚀 TEFAS Analiz Sistemi Başlatılıyor...")
        self.config.print_summary()
        
        # Step 1: Get fund codes
        fund_codes = self._get_fund_codes()
        if not fund_codes:
            raise Exception("🧱 TEFAS verisi alınamadı. İnternet bağlantınızı kontrol edin.")
        
        # Step 2: Prioritize funds
        prioritized_codes = self._prioritize_funds(fund_codes)
        
        # Step 3: Analyze funds
        self._analyze_all_funds(prioritized_codes)
        
        # Step 4: Process results
        summary = self._process_results()
        
        # Step 5: Update panel data
        self._update_panel_data()
        
        return summary
    
    def _get_fund_codes(self) -> List[str]:
        """Get all available fund codes"""
        return self.data_provider.get_fund_codes()
    
    def _prioritize_funds(self, fund_codes: List[str]) -> List[str]:
        """Prioritize portfolio funds and apply MAX_CODES limit"""
        portfolio_funds = self.panel_manager.get_portfolio_funds()
        
        # Separate portfolio and other funds
        portfolio_codes = [code for code in portfolio_funds if code in fund_codes]
        other_codes = [code for code in fund_codes if code not in portfolio_funds]
        
        # Prioritize portfolio funds
        prioritized_codes = portfolio_codes + other_codes
        
        # Apply MAX_CODES limit if specified
        if self.config.analysis.max_codes:
            prioritized_codes = prioritized_codes[:self.config.analysis.max_codes]
        
        self.stats.total_funds = len(fund_codes)
        
        print(f"\n📊 TEFAS Fon Tarama | OOP VERSIYON")
        print(f"📅 Analiz Tarihi: {date.today()}")
        print(f"📈 Toplam Fonlar: {len(fund_codes):,}")
        print(f"🎯 Portföy Fonları: {len(portfolio_codes)} (öncelik)")
        print(f"📊 Diğer Fonlar: {len(other_codes):,}")
        print(f"🔍 Analiz Edilecek: {len(prioritized_codes):,}")
        print(f"📏 Likidite Filtresi: Min. {self.config.filters.min_investors} yatırımcı")
        
        return prioritized_codes
    
    def _analyze_all_funds(self, fund_codes: List[str]):
        """Analyze all funds in the list"""
        portfolio_funds = self.panel_manager.get_portfolio_funds()
        
        print(f"\n🚀 Analiz başlatılıyor... {len(fund_codes)} fon")
        print("─" * 60)
        
        for i, fund_code in enumerate(fund_codes, 1):
            self._show_progress(i, len(fund_codes), fund_code, portfolio_funds)
            
            # Get fund data
            start_date = (date.today() - timedelta(days=self.config.analysis.history_days)).isoformat()
            end_date = (date.today() - timedelta(days=self.config.analysis.end_offset_days)).isoformat()
            
            df = self.data_provider.get_fund_data(fund_code, start_date, end_date)
            
            # Extract fund company from title (if available in data)
            fund_company = 'Bilinmeyen'
            if not df.empty and 'title' in df.columns and not df['title'].isna().all():
                fund_title = df['title'].iloc[-1]  # Get latest title
                fund_company = self.data_provider.extract_fund_company(fund_title)
            
            if df.empty:
                continue
            
            # Check if fund should be analyzed
            if not self.data_provider.should_analyze_fund(df, fund_code, portfolio_funds):
                # Track filtered funds
                investor_count = self.data_provider.get_latest_investor_count(df)
                if investor_count < self.config.filters.min_investors:
                    self.stats.filtered_out += 1
                    if self.stats.filtered_out <= 3:  # Show first 3 filtered funds
                        print(f"⚠️ {fund_code}: {investor_count} yatırımcı (< {self.config.filters.min_investors}) - atlandı")
                continue
            
            # Perform technical analysis
            analysis_result = self.technical_analyzer.analyze_fund(df, fund_code)
            self.analysis_results.append(analysis_result)
            
            # Get fund statistics
            fund_stats = self.data_provider.get_fund_statistics(df)
            
            # Store company info for later use
            self.fund_companies[fund_code] = fund_company
            
            # Store portfolio analysis
            if fund_code in portfolio_funds:
                self._add_portfolio_analysis(analysis_result, fund_stats, fund_company)
            
            # Check for declining trends
            if analysis_result.decline_score >= self.config.analysis.early_momentum_min_score:
                self._add_declining_fund(analysis_result)
            
            # Analyze case patterns
            case_results = self.technical_analyzer.analyze_case_patterns(df, fund_code)
            self._add_case_results(case_results)
            
            self.stats.processed_funds += 1
            
            # Sleep between requests
            if self.config.analysis.sleep_between > 0:
                time.sleep(self.config.analysis.sleep_between)
    
    def _show_progress(self, current: int, total: int, fund_code: str, portfolio_funds: List[str]):
        """Show analysis progress"""
        if current % 50 == 0 or current == total:
            rate = self.stats.processing_rate
            eta = (total - current) / rate if rate > 0 else 0
            
            status_icon = "🎯" if fund_code in portfolio_funds else "📊"
            print(f"{status_icon} {current:,}/{total:,} ({current/total*100:.1f}%) | "
                  f"Hız: {rate:.1f} fon/sn | Kalan: {eta/60:.1f}dk")
    
    def _add_portfolio_analysis(self, result: AnalysisResult, fund_stats: Dict[str, Any], fund_company: str = 'Bilinmeyen'):
        """Add fund to portfolio analysis"""
        trend_status, criteria_text = self.technical_analyzer.determine_trend_status(result)
        
        self.portfolio_analysis.append({
            "Fon": result.fund_code,
            "Şirket": fund_company,
            "Trend_Status": trend_status,
            "Yükselis_Skor": result.score,
            "Düşüş_Skor": result.decline_score,
            "Comprehensive_Score": result.score,  # Add comprehensive score for HTML display
            "Skor": result.score,  # Also add as 'Skor' for compatibility
            "Kriterler": criteria_text,
            "RSI": result.rsi,
            "MACD": result.macd,
            "Signal": result.macd_signal,
            "Fiyat": result.price,
            "Yatırımcı": fund_stats['investor_count'],
            "Yatırımcı_Değişim": fund_stats['investor_change_week'],
            "Hacim": fund_stats['volume'],
            "Hacim_Değişim": fund_stats['volume_change_week'],
            # Add additional metrics for HTML display
            "volatility": fund_stats.get('volatility', 'N/A'),
            "sharpe_ratio": fund_stats.get('sharpe_ratio', 'N/A'),
            "positive_days_5": fund_stats.get('positive_days_5', 'N/A'),
            "performance_1d": fund_stats.get('performance_1d', 0),
            "performance_3d": fund_stats.get('performance_3d', 0),
            "performance_7d": fund_stats.get('performance_7d', 0)
        })
    
    def _add_declining_fund(self, result: AnalysisResult):
        """Add fund to declining funds list"""
        self.declining_funds.append({
            "Fon": result.fund_code,
            "Skor": result.decline_score,
            "Kriterler": ", ".join(result.decline_criteria)
        })
        self.stats.portfolio_alerts += 1
    
    def _add_case_results(self, case_results: Dict[str, Any]):
        """Add case pattern results"""
        for case_type, case_data in case_results.items():
            if case_type in self.case_results:
                self.case_results[case_type].append(case_data)
    
    def _process_results(self) -> Dict[str, Any]:
        """Process and categorize analysis results"""
        print("\n📊 Sonuçlar işleniyor...")
        
        # Prepare fund statistics for categorization (use cached company data)
        fund_statistics = {}
        
        for result in self.analysis_results:
            # Get fund data for statistics
            start_date = (date.today() - timedelta(days=self.config.analysis.history_days)).isoformat()
            end_date = (date.today() - timedelta(days=self.config.analysis.end_offset_days)).isoformat()
            df = self.data_provider.get_fund_data(result.fund_code, start_date, end_date)
            
            fund_statistics[result.fund_code] = self.data_provider.get_fund_statistics(df)
        
        # Categorize candidates (use cached company data)
        early_momentum, trend_candidates = self.technical_analyzer.categorize_candidates(
            self.analysis_results, fund_statistics, self.fund_companies
        )
        
        self.stats.early_momentum_count = len(early_momentum)
        self.stats.trend_candidates_count = len(trend_candidates)
        
        # Print results summary
        self._print_results_summary(early_momentum, trend_candidates)
        
        return {
            "early_momentum": early_momentum,
            "trend_candidates": trend_candidates,
            "portfolio_analysis": self.portfolio_analysis,
            "declining_funds": self.declining_funds,
            "case_results": self.case_results,
            "stats": self.stats
        }
    
    def _print_results_summary(self, early_momentum: List[CandidateResult], trend_candidates: List[CandidateResult]):
        """Print analysis results summary"""
        print("\n" + "="*60)
        print("📈 TEFAS ANALİZ SONUÇLARI")
        print("="*60)
        
        print(f"⏱️ Toplam Süre: {self.stats.elapsed_time/60:.1f} dakika")
        print(f"📊 İncelenen Fon: {self.stats.total_funds:,}")
        print(f"✅ Analiz Edilen: {self.stats.processed_funds:,}")
        print(f"📏 Filtrelenen: {self.stats.filtered_out:,} (< {self.config.filters.min_investors} yatırımcı)")
        print(f"🚀 Erken Momentum: {len(early_momentum)} aday")
        print(f"💎 Güçlü Trend: {len(trend_candidates)} aday")
        print(f"⚠️ Portföy Uyarısı: {len(self.declining_funds)} fon")
        print(f"⚡ İşlem Hızı: {self.stats.processing_rate:.1f} fon/saniye")
        
        # Show early momentum candidates
        if early_momentum:
            print(f"\n🟡 ERKEN MOMENTUM ADAYLARI ({len(early_momentum)}):")
            for candidate in sorted(early_momentum, key=lambda x: x.score, reverse=True):
                print(f"  • {candidate.fund_code}: Skor {candidate.score} | RSI {candidate.rsi}")
        
        # Show trend candidates
        if trend_candidates:
            print(f"\n💎 GÜÇLÜ TREND ADAYLARI ({len(trend_candidates)}):")
            for candidate in sorted(trend_candidates, key=lambda x: x.score, reverse=True):
                print(f"  • {candidate.fund_code}: Skor {candidate.score} | RSI {candidate.rsi}")
    
    def _update_panel_data(self):
        """Update panel data with analysis results"""
        # Get current results (use cached company data)
        fund_statistics = {}
        early_momentum, trend_candidates = self.technical_analyzer.categorize_candidates(
            self.analysis_results, fund_statistics, self.fund_companies
        )
        
        # Update panel
        self.panel_manager.update_candidates(early_momentum, trend_candidates)
        
        print(f"💾 Panel güncellendi: {len(early_momentum)} + {len(trend_candidates)} aday")
    
    def get_portfolio_analysis(self) -> List[Dict[str, Any]]:
        """Get portfolio analysis results"""
        return self.portfolio_analysis
    
    def get_declining_funds(self) -> List[Dict[str, Any]]:
        """Get funds with declining trends"""
        return self.declining_funds
    
    def get_case_results(self) -> Dict[str, List]:
        """Get case analysis results"""
        return self.case_results
    
    def get_analysis_stats(self) -> AnalysisStats:
        """Get analysis statistics"""
        return self.stats
    
    def clear_cache(self):
        """Clear all cached data"""
        self.data_provider.clear_cache()
        print("🧹 Cache temizlendi")


if __name__ == "__main__":
    # Test the analyzer
    logging.basicConfig(level=logging.INFO)
    
    analyzer = TefasAnalyzer()
    
    # Run quick test with limited funds
    original_max = analyzer.config.analysis.max_codes
    analyzer.config.analysis.max_codes = 10  # Test with 10 funds
    
    try:
        results = analyzer.run_analysis()
        print(f"✅ Test completed successfully!")
        print(f"Results: {len(results['early_momentum'])} early momentum, {len(results['trend_candidates'])} trend candidates")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Restore original setting
        analyzer.config.analysis.max_codes = original_max