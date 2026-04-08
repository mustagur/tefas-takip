#!/usr/bin/env python3
"""
Test script to verify Excel report generation functionality
"""

from report_generator import ReportGenerator
from technical_analyzer import CandidateResult
from datetime import datetime
import os

def test_excel_generation():
    """Test Excel report generation with sample data"""
    print("🧪 Testing Excel report generation...")
    
    # Initialize report generator
    report_gen = ReportGenerator()
    
    # Sample data
    panel_data = {
        'portfolio_funds': ['DFI', 'TLY', 'YBS']
    }
    
    portfolio_analysis = [
        {
            'Fon': 'DFI',
            'Trend_Status': '🔥 Güçlü Yükseliş',
            'RSI': '68.5',
            'MACD': '0.025',
            'Fiyat': '1.2345',
            'Yatırımcı': 1250,
            'Yatırımcı_Değişim': '+15',
            'Hacim': '15.2M',
            'Hacim_Değişim': '+2.3%',
            'Kriterler': 'MACD pozitif kesişim, RSI güçlü bölgede'
        }
    ]
    
    early_momentum = [
        CandidateResult(
            fund_code='ABC',
            score=2,
            rsi=57.5,
            macd=0.012,
            macd_signal=0.008,
            price=0.8765,
            criteria='RSI 55-60 aralığında, hafif yükseliş sinyali',
            fund_statistics={}
        )
    ]
    
    trend_candidates = [
        CandidateResult(
            fund_code='XYZ',
            score=3.5,
            rsi=72.3,
            macd=0.045,
            macd_signal=0.032,
            price=1.5678,
            criteria='MACD pozitif kesişim + RSI güçlü + Bollinger üst banda yakın',
            fund_statistics={}
        )
    ]
    
    declining_funds = [
        {
            'Fon': 'DEF',
            'Skor': -2.0,
            'Kriterler': 'MACD negatif kesişim, RSI 40 altında'
        }
    ]
    
    case_results = {
        'case1': [{'fund': 'GHI', 'Fon': 'GHI'}],
        'case2': [],
        'case3': [{'fund': 'JKL', 'Fon': 'JKL'}]
    }
    
    # Mock stats
    class MockStats:
        def __init__(self):
            self.elapsed_time = 120.5
            self.total_funds = 1500
            self.processed_funds = 1200
            self.filtered_out = 300
            self.processing_rate = 10.0
            self.early_momentum_count = 1
            self.trend_candidates_count = 1
            self.portfolio_alerts = 1
    
    stats = MockStats()
    
    # Generate Excel report
    excel_file = report_gen.generate_excel_report(
        panel_data=panel_data,
        portfolio_analysis=portfolio_analysis,
        early_momentum=early_momentum,
        trend_candidates=trend_candidates,
        declining_funds=declining_funds,
        case_results=case_results,
        stats=stats
    )
    
    if excel_file and os.path.exists(excel_file):
        print(f"✅ Excel test successful! File created: {excel_file}")
        print(f"📂 File size: {os.path.getsize(excel_file):,} bytes")
        return excel_file
    else:
        print("❌ Excel test failed!")
        return None

if __name__ == "__main__":
    test_file = test_excel_generation()
    if test_file:
        print(f"\n🎉 Excel functionality is working correctly!")
        print(f"📊 Test file: {test_file}")
        print(f"🔍 You can open it with: open {test_file}")
    else:
        print("\n❌ Excel functionality needs debugging")