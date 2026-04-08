#!/usr/bin/env python3
"""
Test script to manually check portfolio funds (TLY, DFI) for case patterns
"""

import pandas as pd
from datetime import datetime, timedelta
from data_provider import FundDataProvider
from technical_analyzer import TechnicalAnalyzer
from config import TefasConfig

def test_portfolio_case_patterns():
    """Test case patterns for portfolio funds"""
    config = TefasConfig()
    data_provider = FundDataProvider()
    analyzer = TechnicalAnalyzer()
    
    portfolio_funds = ['TLY', 'DFI']
    
    # Calculate date range
    end_date = (datetime.now() - timedelta(days=config.analysis.end_offset_days)).date().isoformat()
    start_date = (datetime.now() - timedelta(days=config.analysis.history_days)).date().isoformat()
    
    print(f"📅 Tarih Aralığı: {start_date} -> {end_date}")
    print("=" * 60)
    
    for fund_code in portfolio_funds:
        print(f"\n🔍 {fund_code} Fonu Analizi:")
        print("-" * 30)
        
        try:
            # Get fund data
            fund_data = data_provider.get_fund_data(fund_code, start_date, end_date)
            if fund_data is None or len(fund_data) < 10:
                print(f"❌ {fund_code}: Yetersiz veri")
                continue
            
            print(f"📊 Veri Sayısı: {len(fund_data)} gün")
            
            # Show recent daily changes
            recent_data = fund_data.tail(10)
            print(f"\n📈 Son 10 Günlük Performans:")
            for _, row in recent_data.iterrows():
                date_str = str(row['date'])[:10]
                pct = row.get('pct', 0)
                price = row.get('price', 0)
                print(f"   {date_str}: {pct:+6.2f}% (Fiyat: {price:.4f})")
            
            # Run case analysis
            case_patterns = analyzer.analyze_case_patterns(fund_data, fund_code)
            
            print(f"\n🎯 Case Pattern Sonuçları:")
            if not case_patterns:
                print("   ❌ Hiç pattern bulunamadı")
            else:
                for case_type, pattern_data in case_patterns.items():
                    case_name = {
                        'case1': '① Art Arda ≥%1.0 (3 gün)',
                        'case2': '② Toplam ≥%4.0 (3 gün)', 
                        'case3': '③ Toplam ≥%5.0 (5 gün)'
                    }.get(case_type, case_type)
                    
                    print(f"   ✅ {case_name}")
                    print(f"      • Tarihler: {', '.join([d[:10] for d in pattern_data.get('dates', [])])}")
                    print(f"      • Günlük %: {pattern_data.get('daily_pct', [])}")
                    print(f"      • Kümülatif %: {pattern_data.get('cumulative_pct', 'N/A'):.2f}")
            
            # Manual case checks
            print(f"\n🔬 Manuel Kontrol:")
            
            # Case 1: Son 3 gün art arda ≥1.0%
            case1_data = fund_data.tail(3)
            case1_daily = case1_data['pct'].dropna()
            case1_check = (case1_daily >= 1.0).all() if len(case1_daily) == 3 else False
            print(f"   Case 1 (Art arda ≥1%): {'✅' if case1_check else '❌'}")
            if len(case1_daily) == 3:
                print(f"      Günlük %: {[f'{x:.2f}' for x in case1_daily]}")
            
            # Case 2: Son 3 gün toplam ≥4.0%
            case2_data = fund_data.tail(3)
            case2_daily = case2_data['pct'].dropna()
            case2_cumulative = ((1 + case2_daily / 100.0).prod() - 1) * 100.0 if len(case2_daily) == 3 else 0
            case2_check = case2_cumulative >= 4.0
            print(f"   Case 2 (3gün ≥4%): {'✅' if case2_check else '❌'}")
            print(f"      Kümülatif: {case2_cumulative:.2f}%")
            
            # Case 3: Son 5 gün toplam ≥5.0%
            case3_data = fund_data.tail(5)
            case3_daily = case3_data['pct'].dropna()
            case3_cumulative = ((1 + case3_daily / 100.0).prod() - 1) * 100.0 if len(case3_daily) == 5 else 0
            case3_check = case3_cumulative >= 5.0
            print(f"   Case 3 (5gün ≥5%): {'✅' if case3_check else '❌'}")
            print(f"      Kümülatif: {case3_cumulative:.2f}%")
            
        except Exception as e:
            print(f"❌ {fund_code} analiz hatası: {e}")

if __name__ == "__main__":
    test_portfolio_case_patterns()