#!/usr/bin/env python3
"""
TEFAS Trend Analysis - Object-Oriented Version
Main script that uses the new OOP structure for TEFAS analysis
"""

import sys
import logging
from datetime import datetime
from tefas_analyzer import TefasAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function using the new OOP structure"""
    try:
        print("🚀 TEFAS Trend Analysis - OOP Version")
        print("=" * 60)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Initialize analyzer
        analyzer = TefasAnalyzer()
        
        # Run complete analysis
        results = analyzer.run_analysis()
        
        # Print detailed results
        print_detailed_results(results, analyzer)
        
        print("\n" + "=" * 60)
        print("✅ TEFAS Analysis completed successfully!")
        print("💾 All data saved to panel and reports")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)


def print_detailed_results(results: dict, analyzer: TefasAnalyzer):
    """Print detailed analysis results"""
    
    # Portfolio Analysis
    portfolio_analysis = results.get("portfolio_analysis", [])
    if portfolio_analysis:
        print("\n💼 PORTFÖY ANALİZİ")
        print("─" * 50)
        for fund in portfolio_analysis:
            print(f"\n{fund['Fon']} | {fund['Trend_Status']}")
            print(f"  📊 RSI: {fund['RSI']} | MACD: {fund['MACD']}")
            print(f"  💰 Fiyat: {fund['Fiyat']} TL")
            investor_str = f"{fund['Yatırımcı']:,}" if isinstance(fund['Yatırımcı'], int) else str(fund['Yatırımcı'])
            print(f"  👥 {investor_str} yatırımcı ({fund['Yatırımcı_Değişim']})")
            print(f"  📊 Hacim: {fund['Hacim']} TL ({fund['Hacim_Değişim']})")
            if fund['Kriterler'] != "Belirgin trend sinyali yok":
                print(f"  🎯 {fund['Kriterler']}")
    
    # Early Momentum Candidates
    early_momentum = results.get("early_momentum", [])
    if early_momentum:
        print(f"\n🟡 ERKEN MOMENTUM ADAYLARI ({len(early_momentum)})")
        print("─" * 50)
        for candidate in early_momentum:
            print(f"\n{candidate.fund_code} | Skor: {candidate.score}")
            print(f"  📊 RSI: {candidate.rsi} | MACD: {candidate.macd}")
            print(f"  💰 Fiyat: {candidate.price} TL")
            print(f"  🎯 {candidate.criteria}")
    
    # Trend Candidates
    trend_candidates = results.get("trend_candidates", [])
    if trend_candidates:
        print(f"\n💎 GÜÇLÜ TREND ADAYLARI ({len(trend_candidates)})")
        print("─" * 50)
        for candidate in trend_candidates:
            print(f"\n{candidate.fund_code} | Skor: {candidate.score}")
            print(f"  📊 RSI: {candidate.rsi} | MACD: {candidate.macd}")
            print(f"  💰 Fiyat: {candidate.price} TL")
            print(f"  🎯 {candidate.criteria}")
    
    # Declining Funds Warning
    declining_funds = results.get("declining_funds", [])
    if declining_funds:
        print(f"\n⚠️ PORTFÖY UYARISI ({len(declining_funds)} fon)")
        print("─" * 50)
        for fund in declining_funds:
            print(f"🔴 {fund['Fon']}: {fund['Kriterler']} (Skor: {fund['Skor']})")
    
    # Case Results
    case_results = results.get("case_results", {})
    print_case_results(case_results)
    
    # Final Statistics
    stats = results.get("stats")
    if stats:
        print(f"\n📊 ANALİZ İSTATİSTİKLERİ")
        print("─" * 50)
        print(f"⏱️ Toplam Süre: {stats.elapsed_time/60:.1f} dakika")
        print(f"📈 Toplam Fonlar: {stats.total_funds:,}")
        print(f"✅ Analiz Edilen: {stats.processed_funds:,}")
        print(f"📏 Filtrelenen: {stats.filtered_out:,}")
        print(f"🚀 Erken Momentum: {stats.early_momentum_count}")
        print(f"💎 Güçlü Trend: {stats.trend_candidates_count}")
        print(f"⚠️ Portföy Uyarısı: {stats.portfolio_alerts}")
        print(f"⚡ İşlem Hızı: {stats.processing_rate:.1f} fon/saniye")


def print_case_results(case_results: dict):
    """Print case analysis results"""
    case_titles = {
        "case1": "① ARDIŞIK GÜNLÜK KAZANÇLAR",
        "case2": "② KISA VADELİ BİRİKİMLİ KAZANÇ",
        "case3": "③ HAFTALIK BİRİKİMLİ KAZANÇ"
    }
    
    for case_type, results in case_results.items():
        if results:
            title = case_titles.get(case_type, f"Case {case_type}")
            print(f"\n{title} ({len(results)} fon)")
            print("─" * 50)
            
            for result in results:
                print(f"\nFon: {result['fund']}")
                print(f"Tarihler: {result['dates']}")
                print(f"Günlük %: {result['daily_pct']}")
                print(f"Kümülatif: %{result['cumulative_pct']}")


def test_oop_structure():
    """Quick test of the OOP structure"""
    print("🧪 OOP Yapısı Test Ediliyor...")
    
    try:
        analyzer = TefasAnalyzer()
        
        # Test with 50 funds for better coverage
        analyzer.config.analysis.max_codes = 50
        
        results = analyzer.run_analysis()
        
        print("✅ OOP test başarılı!")
        print(f"📊 Sonuçlar: {len(results)} kategori")
        
        return True
        
    except Exception as e:
        print(f"❌ OOP test başarısız: {e}")
        return False


if __name__ == "__main__":
    # Check if this is a test run
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = test_oop_structure()
        sys.exit(0 if success else 1)
    else:
        main()