#!/usr/bin/env python3
"""
TEFAS Trend Analysis - Object-Oriented Version
Version: OOP 2.0

Main Script for running TEFAS fund analysis with modular OOP architecture
"""

import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Any

# Import OOP modules
from config import config
from data_provider import FundDataProvider
from technical_analyzer import TechnicalAnalyzer, CandidateResult
from panel_manager import PanelManager
from report_generator import ReportGenerator
from email_reporter import EmailReporter


@dataclass
class AnalysisStats:
    """Statistics tracking for analysis run"""
    start_time: float
    elapsed_time: float
    total_funds: int
    processed_funds: int
    filtered_out: int
    processing_rate: float
    early_momentum_count: int = 0
    trend_candidates_count: int = 0
    portfolio_alerts: int = 0


class TefasAnalyzer:
    """Main orchestration class for TEFAS analysis"""
    
    def __init__(self):
        self.config = config
        self.data_provider = FundDataProvider()
        self.technical_analyzer = TechnicalAnalyzer()
        self.panel_manager = PanelManager()
        self.report_generator = ReportGenerator()
        self.email_reporter = EmailReporter()
        self.stats = None
        
        # Print system info
        print("🚀 TEFAS OOP v2.0 Sistemi Başlatılıyor...")
        print(f"📁 Veri Dizini: {self.config.files.data_dir}")
        print(f"📊 Minimum Yatırımcı Sayısı: {self.config.analysis.min_investors:,}")
        print(f"🎯 Erken Momentum Skoru: {self.config.analysis.early_momentum_min_score}-{self.config.analysis.early_momentum_max_score}")
        print(f"💎 Güçlü Trend Skoru: {self.config.analysis.trend_min_score}+")
        print(f"📧 Email Yapılandırması: {'✅' if self.email_reporter.can_send_email() else '❌ (Simülasyon)'}")
        print("─" * 60)

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete TEFAS analysis pipeline"""
        start_time = time.time()
        print(f"\n📅 Analiz Başlangıcı: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        
        try:
            # Step 1: Load fund codes
            print("📋 1. Fon kodları yükleniyor...")
            fund_codes = self.data_provider.get_fund_codes()
            print(f"   ✅ {len(fund_codes):,} fon kodu yüklendi")
            
            # Step 2: Get portfolio data
            print("\n💼 2. Portföy verileri alınıyor...")
            panel_data = self.panel_manager.get_panel_data()
            portfolio_funds = panel_data.get('portfolio_funds', [])
            print(f"   ✅ {len(portfolio_funds)} portföy fonu tespit edildi")
            
            # Step 3: Analyze portfolio
            print("\n🔍 3. Portföy analizi yapılıyor...")
            portfolio_analysis, declining_funds = self._analyze_portfolio(portfolio_funds)
            print(f"   ✅ Portföy analizi tamamlandı, {len(declining_funds)} uyarı")
            
            # Step 4: Find candidates from all funds
            print(f"\n🎯 4. {len(fund_codes):,} fon arasından aday aranıyor...")
            early_momentum, trend_candidates, analysis_stats = self._find_candidates(fund_codes)
            
            # Step 5: Case analysis
            print(f"\n📈 5. Bütün fonlar üzerinde case analizleri yapılıyor...")
            case_results = self._run_case_analysis(fund_codes)  # Analyze ALL funds for cases
            print(f"   ✅ Case analizleri tamamlandı")
            
            # Create final stats
            elapsed_time = time.time() - start_time
            self.stats = AnalysisStats(
                start_time=start_time,
                elapsed_time=elapsed_time,
                total_funds=len(fund_codes),
                processed_funds=analysis_stats['processed'],
                filtered_out=analysis_stats['filtered'],
                processing_rate=analysis_stats['processed'] / elapsed_time if elapsed_time > 0 else 0,
                early_momentum_count=len(early_momentum),
                trend_candidates_count=len(trend_candidates),
                portfolio_alerts=len(declining_funds)
            )
            
            print(f"\n🏁 Analiz Tamamlandı: {elapsed_time/60:.1f} dakika")
            print(f"📊 İstatistikler: {analysis_stats['processed']:,} işlendi, {analysis_stats['filtered']:,} filtrelendi")
            print(f"🎯 Sonuçlar: {len(early_momentum)} erken momentum, {len(trend_candidates)} güçlü trend")
            
            # Step 6: Generate reports
            print("\n📄 6. Raporlar oluşturuluyor...")
            html_file = self.report_generator.generate_html_report(
                panel_data=panel_data,
                portfolio_analysis=portfolio_analysis,
                early_momentum=early_momentum,
                trend_candidates=trend_candidates,
                declining_funds=declining_funds,
                case_results=case_results,
                stats=self.stats
            )
            
            # Generate Excel report
            excel_file = self.report_generator.generate_excel_report(
                panel_data=panel_data,
                portfolio_analysis=portfolio_analysis,
                early_momentum=early_momentum,
                trend_candidates=trend_candidates,
                declining_funds=declining_funds,
                case_results=case_results,
                stats=self.stats
            )
            
            # Step 7: Send email
            print("\n📧 7. Email gönderiliyor...")
            email_sent = self.email_reporter.send_report_email(
                html_file=html_file,
                early_momentum_count=len(early_momentum),
                trend_candidates_count=len(trend_candidates),
                portfolio_alerts=len(declining_funds),
                stats=self.stats
            )
            
            return {
                'panel_data': panel_data,
                'portfolio_analysis': portfolio_analysis,
                'early_momentum': early_momentum,
                'trend_candidates': trend_candidates,
                'declining_funds': declining_funds,
                'case_results': case_results,
                'stats': self.stats,
                'html_file': html_file,
                'excel_file': excel_file,
                'email_sent': email_sent
            }
            
        except Exception as e:
            print(f"❌ Analiz hatası: {e}")
            raise

    def _analyze_portfolio(self, portfolio_funds: List[str]) -> tuple:
        """Analyze portfolio funds and detect declining ones"""
        portfolio_analysis = []
        declining_funds = []
        
        for fund_code in portfolio_funds:
            try:
                # Calculate date range
                end_date = (datetime.now() - timedelta(days=self.config.analysis.end_offset_days)).date().isoformat()
                start_date = (datetime.now() - timedelta(days=self.config.analysis.history_days)).date().isoformat()
                
                # Get fund data
                fund_data = self.data_provider.get_fund_data(fund_code, start_date, end_date)
                if fund_data is None or len(fund_data) < 20:
                    continue
                
                # Extract fund company from title
                fund_company = 'Bilinmeyen'
                if not fund_data.empty and 'title' in fund_data.columns and not fund_data['title'].isna().all():
                    fund_title = fund_data['title'].iloc[-1]
                    fund_company = self.data_provider.extract_fund_company(fund_title)
                
                # Analyze fund
                analysis_result = self.technical_analyzer.analyze_fund(fund_data, fund_code)
                
                # Get additional info
                latest_price = fund_data.iloc[-1]['price']
                latest_investors = fund_data.iloc[-1].get('number_of_investors', 0)
                latest_volume = fund_data.iloc[-1].get('market_cap', 0)
                
                # Calculate investor change
                prev_investors = fund_data.iloc[-2].get('number_of_investors', 0) if len(fund_data) > 1 else latest_investors
                investor_change = latest_investors - prev_investors
                investor_change_str = f"+{investor_change}" if investor_change > 0 else str(investor_change)
                
                # Calculate volume change
                prev_volume = fund_data.iloc[-2].get('market_cap', 0) if len(fund_data) > 1 else latest_volume
                volume_change = latest_volume - prev_volume
                volume_change_pct = (volume_change / prev_volume * 100) if prev_volume > 0 else 0
                volume_change_str = f"+{volume_change_pct:.1f}%" if volume_change > 0 else f"{volume_change_pct:.1f}%"
                
                # Determine trend status using technical analyzer's consistent logic
                trend_status, criteria_text = self.technical_analyzer.determine_trend_status(analysis_result)
                
                # Check for declining funds
                if analysis_result.decline_score >= self.config.analysis.early_momentum_min_score:
                    declining_funds.append({
                        'Fon': fund_code,
                        'Skor': analysis_result.decline_score,
                        'Kriterler': ", ".join(analysis_result.decline_criteria) if analysis_result.decline_criteria else "Düşüş sinyali"
                    })
                
                # Get performance statistics
                fund_stats = self.data_provider.get_fund_statistics(fund_data)
                
                portfolio_analysis.append({
                    'Fon': fund_code,
                    'Şirket': fund_company,
                    'Fiyat': f"{latest_price:.4f}",
                    'RSI': analysis_result.rsi,
                    'MACD': analysis_result.macd,
                    'Yatırımcı': latest_investors,
                    'Yatırımcı_Değişim': investor_change_str,
                    'Hacim': f"{latest_volume/1000000:.1f}M" if latest_volume > 1000000 else f"{latest_volume/1000:.0f}K",
                    'Hacim_Değişim': volume_change_str,
                    'Trend_Status': trend_status,
                    'Kriterler': criteria_text,  # Use criteria from technical analyzer
                    'Comprehensive_Score': analysis_result.score,  # Add comprehensive score
                    'Skor': analysis_result.score,  # Also add as 'Skor' for compatibility
                    'performance_1d': fund_stats.get('performance_1d', 0),
                    'performance_3d': fund_stats.get('performance_3d', 0),
                    'performance_7d': fund_stats.get('performance_7d', 0),
                    'volatility': fund_stats.get('volatility', 'N/A'),
                    'sharpe_ratio': fund_stats.get('sharpe_ratio', 'N/A'),
                    'positive_days_5': fund_stats.get('positive_days_5', 'N/A')
                })
                
            except Exception as e:
                print(f"   ⚠️ {fund_code} portföy analiz hatası: {e}")
                continue
        
        return portfolio_analysis, declining_funds

    def _find_candidates(self, fund_codes: List[str]) -> tuple:
        """Find early momentum and trend candidates from fund list"""
        early_momentum = []
        trend_candidates = []
        processed = 0
        filtered = 0
        
        # Apply MAX_CODES limit for testing if set, but ensure portfolio funds are always included
        if self.config.analysis.max_codes and self.config.analysis.max_codes > 0:
            # Get portfolio funds
            portfolio_funds = self.panel_manager.get_portfolio_funds()
            
            # Start with portfolio funds
            portfolio_codes = [code for code in portfolio_funds if code in fund_codes]
            
            # Add other funds up to max_codes limit
            other_codes = [code for code in fund_codes if code not in portfolio_funds]
            remaining_slots = max(0, self.config.analysis.max_codes - len(portfolio_codes))
            selected_other_codes = other_codes[:remaining_slots]
            
            fund_codes = portfolio_codes + selected_other_codes
            print(f"   🚧 Test modu: {len(fund_codes)} fon analiz edilecek (portföy: {len(portfolio_codes)})")
        
        for i, fund_code in enumerate(fund_codes):
            if i % 100 == 0:
                print(f"   📈 İşlenen: {i:,}/{len(fund_codes):,} (%{i/len(fund_codes)*100:.1f})")
            
            try:
                # Calculate date range
                end_date = (datetime.now() - timedelta(days=self.config.analysis.end_offset_days)).date().isoformat()
                start_date = (datetime.now() - timedelta(days=self.config.analysis.history_days)).date().isoformat()
                
                # Get fund data
                fund_data = self.data_provider.get_fund_data(fund_code, start_date, end_date)
                if fund_data is None or len(fund_data) < 30:
                    filtered += 1
                    continue
                
                # Extract fund company from title
                fund_company = 'Bilinmeyen'
                if not fund_data.empty and 'title' in fund_data.columns and not fund_data['title'].isna().all():
                    fund_title = fund_data['title'].iloc[-1]
                    fund_company = self.data_provider.extract_fund_company(fund_title)
                
                # Apply investor filter (skip portfolio funds)
                latest_investors = fund_data.iloc[-1].get('number_of_investors', 0)
                if latest_investors < self.config.analysis.min_investors:
                    # Check if it's a portfolio fund (allow these through)
                    if not fund_code.startswith(('TRE', 'TEB', 'ZIR', 'GEL', 'TGE')):
                        filtered += 1
                        continue
                
                processed += 1
                
                # Analyze fund
                analysis_result = self.technical_analyzer.analyze_fund(fund_data, fund_code)
                
                # Get fund statistics for enhanced candidate info
                fund_stats = self.data_provider.get_fund_statistics(fund_data)
                
                if analysis_result.score >= self.config.analysis.trend_min_score:
                    # Apply momentum filter for trend candidates too
                    if analysis_result.has_recent_momentum:
                        # Convert to CandidateResult for trend candidates with enhanced stats
                        candidate = CandidateResult(
                            fund_code=analysis_result.fund_code,
                            score=analysis_result.score,
                            criteria=", ".join(analysis_result.criteria) if analysis_result.criteria else "Güçlü trend sinyali",
                            rsi=analysis_result.rsi,
                            macd=analysis_result.macd,
                            macd_signal=analysis_result.macd_signal,
                            price=analysis_result.price,
                            fund_statistics=fund_stats,
                            company=fund_company
                        )
                        trend_candidates.append(candidate)
                elif (self.config.analysis.early_momentum_min_score <= 
                      analysis_result.score < self.config.analysis.trend_min_score):
                    # Apply momentum filter for early momentum candidates
                    if analysis_result.has_recent_momentum:
                        # Early momentum candidates: Keep original score and RSI (50-75 range)
                        early_result = CandidateResult(
                            fund_code=analysis_result.fund_code,
                            score=analysis_result.score,  # Keep original comprehensive score
                            rsi=analysis_result.rsi,      # Keep original RSI
                            macd=analysis_result.macd,
                            macd_signal=analysis_result.macd_signal,
                            price=analysis_result.price,
                            criteria=", ".join(analysis_result.criteria) if analysis_result.criteria else "Erken momentum sinyali",
                            fund_statistics=fund_stats,
                            company=fund_company
                        )
                        early_momentum.append(early_result)
                    
            except Exception as e:
                print(f"   ⚠️ {fund_code} analiz hatası: {e}")
                filtered += 1
                continue
        
        # Sort by score
        early_momentum.sort(key=lambda x: x.score, reverse=True)
        trend_candidates.sort(key=lambda x: x.score, reverse=True)
        
        print(f"   ✅ {processed:,} fon analiz edildi, {filtered:,} filtrelendi")
        print(f"   🟡 {len(early_momentum)} erken momentum adayı")
        print(f"   💎 {len(trend_candidates)} güçlü trend adayı")
        
        return early_momentum, trend_candidates, {
            'processed': processed,
            'filtered': filtered
        }

    def _run_case_analysis(self, fund_codes: List[str]) -> Dict[str, List]:
        """Run comprehensive case analysis on qualifying funds (respects max_codes)"""
        case_results = {
            'case1': [],  # Son 3 işlem günü Art Arda ≥ %1.0
            'case2': [],  # Son 3 işlem günü Toplam ≥ %4.0
            'case3': []   # Son 5 işlem günü Toplam ≥ %5.0
        }
        
        # Apply MAX_CODES limit for case analysis but ensure portfolio funds are always included
        analysis_fund_codes = fund_codes.copy()
        if self.config.analysis.max_codes and self.config.analysis.max_codes > 0:
            # Get portfolio funds
            portfolio_funds = self.panel_manager.get_portfolio_funds()
            
            # Start with portfolio funds
            portfolio_codes = [code for code in portfolio_funds if code in fund_codes]
            
            # Add other funds up to max_codes limit
            other_codes = [code for code in fund_codes if code not in portfolio_funds]
            remaining_slots = max(0, self.config.analysis.max_codes - len(portfolio_codes))
            selected_other_codes = other_codes[:remaining_slots]
            
            analysis_fund_codes = portfolio_codes + selected_other_codes
            
            print(f"   🔍 Case analizi: {len(analysis_fund_codes):,} fon analiz ediliyor (max_codes: {self.config.analysis.max_codes}, portföy: {len(portfolio_codes)})...")
        else:
            print(f"   🔍 Case analizi: {len(fund_codes):,} fon üzerinde kapsamlı analiz başlatılıyor...")
        processed = 0
        filtered_out = 0
        
        for i, fund_code in enumerate(analysis_fund_codes):
            # Progress indicator - adjust frequency based on dataset size
            progress_interval = 50 if len(analysis_fund_codes) <= 500 else 200
            if i % progress_interval == 0:
                print(f"   📈 Case analizi: {i:,}/{len(analysis_fund_codes):,} (%{i/len(analysis_fund_codes)*100:.1f})")
            
            try:
                # Calculate date range
                end_date = (datetime.now() - timedelta(days=self.config.analysis.end_offset_days)).date().isoformat()
                start_date = (datetime.now() - timedelta(days=self.config.analysis.history_days)).date().isoformat()
                
                # Get fund data
                fund_data = self.data_provider.get_fund_data(fund_code, start_date, end_date)
                if fund_data is None or len(fund_data) < 10:
                    filtered_out += 1
                    continue
                
                # Apply investor filter (but allow portfolio funds through)
                latest_investors = fund_data.iloc[-1].get('number_of_investors', 0)
                if latest_investors < self.config.analysis.min_investors:
                    # Check if it's a portfolio fund or known prefix (allow these through)
                    portfolio_funds = self.panel_manager.get_portfolio_funds()
                    if fund_code not in portfolio_funds and not fund_code.startswith(('TRE', 'TEB', 'ZIR', 'GEL', 'TGE')):
                        filtered_out += 1
                        continue
                
                processed += 1
                
                # Extract fund company from title
                fund_company = 'Bilinmeyen'
                if not fund_data.empty and 'title' in fund_data.columns and not fund_data['title'].isna().all():
                    fund_title = fund_data['title'].iloc[-1]
                    fund_company = self.data_provider.extract_fund_company(fund_title)
                
                # Analyze fund for technical indicators and score
                analysis_result = self.technical_analyzer.analyze_fund(fund_data, fund_code)
                
                # Get fund statistics
                fund_stats = self.data_provider.get_fund_statistics(fund_data)
                
                # Run case analysis using technical analyzer
                case_patterns = self.technical_analyzer.analyze_case_patterns(fund_data, fund_code)
                
                # Add enhanced data to results
                for case_type, pattern_data in case_patterns.items():
                    if case_type in case_results:
                        # Enhance pattern data with technical analysis
                        enhanced_pattern = pattern_data.copy()
                        enhanced_pattern.update({
                            'company': fund_company,
                            'score': analysis_result.score,
                            'rsi': analysis_result.rsi,
                            'macd': analysis_result.macd,
                            'macd_signal': analysis_result.macd_signal,
                            'price': analysis_result.price,
                            'criteria': ', '.join(analysis_result.criteria) if analysis_result.criteria else 'Pattern sinyali',
                            'investor_count': fund_stats.get('investor_count', 'N/A'),
                            'investor_change_week': fund_stats.get('investor_change_week', 'N/A'),
                            'volume': fund_stats.get('volume', 'N/A'),
                            'volume_change_week': fund_stats.get('volume_change_week', 'N/A'),
                            'performance_1d': fund_stats.get('performance_1d', 0),
                            'performance_3d': fund_stats.get('performance_3d', 0),
                            'performance_7d': fund_stats.get('performance_7d', 0)
                        })
                        case_results[case_type].append(enhanced_pattern)
                
            except Exception as e:
                continue  # Skip problematic funds
        
        # Print comprehensive summary
        total_patterns = sum(len(patterns) for patterns in case_results.values())
        print(f"   📈 CASE ANALİZ SONUÇLARI")
        print(f"   ───────────────────────────")
        print(f"   🔍 Tarama kapsamı: {len(analysis_fund_codes):,} fon{' (max_codes limit)' if self.config.analysis.max_codes else ''}")
        print(f"   ✅ Analiz edilebilen: {processed:,} fon")
        print(f"   ❌ Filtrelenen: {filtered_out:,} fon")
        print(f"   📈 Analiz oranı: %{(processed/len(analysis_fund_codes)*100):.1f}")
        print()
        
        # Show detailed case results
        print(f"   ① Case 1 (3 gün Art Arda ≥%1.0): {len(case_results['case1'])} fon")
        if case_results['case1']:
            case1_funds = [r['fund'] for r in case_results['case1']]
            print(f"      └─ {', '.join(case1_funds[:15])}{'...' if len(case1_funds) > 15 else ''}")
            
        print(f"   ② Case 2 (3 gün Toplam ≥%4.0): {len(case_results['case2'])} fon")
        if case_results['case2']:
            case2_funds = [r['fund'] for r in case_results['case2']]
            print(f"      └─ {', '.join(case2_funds[:15])}{'...' if len(case2_funds) > 15 else ''}")
            
        print(f"   ③ Case 3 (5 gün Toplam ≥%5.0): {len(case_results['case3'])} fon")
        if case_results['case3']:
            case3_funds = [r['fund'] for r in case_results['case3']]
            print(f"      └─ {', '.join(case3_funds[:15])}{'...' if len(case3_funds) > 15 else ''}")
            
        print()
        print(f"   🎆 TOPLAM ÖZEL PATTERN: {total_patterns} adet")
        
        # Show portfolio fund results specifically
        portfolio_funds = self.panel_manager.get_portfolio_funds()
        portfolio_with_patterns = []
        for pf in portfolio_funds:
            fund_patterns = []
            for case_type, results in case_results.items():
                if any(r['fund'] == pf for r in results):
                    fund_patterns.append(case_type)
            if fund_patterns:
                portfolio_with_patterns.append(f"{pf} ({','.join(fund_patterns)})")
        
        if portfolio_with_patterns:
            print(f"   💼 Portföy fonlarında pattern: {', '.join(portfolio_with_patterns)}")
        
        return case_results


def main():
    """Main function"""
    analyzer = TefasAnalyzer()
    
    try:
        results = analyzer.run_full_analysis()
        print(f"\n🎉 Tüm işlemler tamamlandı!")
        print(f"📄 HTML Rapor: {results.get('html_file', 'Oluşturulamadı')}")
        print(f"📊 Excel Rapor: {results.get('excel_file', 'Oluşturulamadı')}")
        print(f"📧 Email: {'Gönderildi' if results.get('email_sent') else 'Simülasyon'}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"\n❌ Kritik hata: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()