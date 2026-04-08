#!/usr/bin/env python3
"""
TEFAS Data Provider Module
Handles data fetching from TEFAS API, caching, and data validation
"""

from tefas import Crawler
import pandas as pd
import time
import logging
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from config import config

logger = logging.getLogger(__name__)


class FundDataProvider:
    """Handles all TEFAS data fetching operations"""
    
    def __init__(self):
        self.crawler = Crawler()
        self.cache = {}  # Simple in-memory cache
        
    def get_fund_codes(self) -> List[str]:
        """
        Get all available fund codes from TEFAS
        Tries multiple dates to handle weekends/holidays
        """
        print("🔍 Fon kodları alınıyor...")
        
        for days_back in range(0, 10):
            try:
                test_date = (date.today() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                print(f"🗺 Tarih deneniyor: {test_date}")
                
                all_funds = self.crawler.fetch(test_date)
                
                if not all_funds.empty and 'code' in all_funds.columns:
                    codes = sorted(all_funds['code'].unique().tolist())
                    print(f"✅ {len(codes)} fon kodu bulundu ({test_date})")
                    return codes
                else:
                    print(f"⚠️ {test_date}: Boş sonuç")
                    
            except Exception as e:
                print(f"⚠️ {test_date}: Hata - {e}")
        
        print("❌ Tüm tarihler denendi, hiçbir gün veri bulunamadı")
        return []
    
    def get_fund_data(self, fund_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch fund data for given date range
        Includes caching and retry logic
        """
        cache_key = f"{fund_code}_{start_date}_{end_date}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key].copy()
        
        for attempt in range(config.analysis.retry_limit):
            try:
                df = self.crawler.fetch(start_date, end_date, fund_code)
                if df.empty:
                    return pd.DataFrame()
                
                # Clean and process data
                df = self._clean_fund_data(df)
                
                # Cache the result
                self.cache[cache_key] = df.copy()
                
                logger.debug(f"{fund_code}: {len(df)} günlük veri alındı")
                return df
                
            except Exception as e:
                logger.warning(f"{fund_code} veri çekme hatası (deneme {attempt + 1}/{config.analysis.retry_limit}): {e}")
                if attempt < config.analysis.retry_limit - 1:
                    time.sleep(0.5)
        
        return pd.DataFrame()
    
    def _clean_fund_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare fund data"""
        if df.empty:
            return df
        
        # Convert dates and sort
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values("date", ascending=True).dropna(subset=["price"]).reset_index(drop=True)
        
        # Calculate percentage changes
        df["pct"] = df["price"].pct_change() * 100.0
        
        return df
    
    def get_fund_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate fund statistics (investor count, volume, etc.)"""
        if df.empty or len(df) < 7:
            return {
                'investor_count': 'N/A',
                'investor_change_week': 'N/A', 
                'volume': 'N/A',
                'volume_change_week': 'N/A',
                'performance_1d': 0.0,
                'performance_3d': 0.0,
                'performance_7d': 0.0
            }
        
        # Get latest and week-ago data
        latest = df.iloc[-1]
        week_ago = df.iloc[-7] if len(df) >= 7 else df.iloc[0]
        
        # Investor count and changes
        current_investors = latest.get('number_of_investors', 0) or 0
        week_investors = week_ago.get('number_of_investors', 0) or 0
        investor_change = current_investors - week_investors
        investor_change_sign = '+' if investor_change > 0 else ''
        
        # Volume and changes
        current_volume = latest.get('market_cap', 0) or 0
        week_volume = week_ago.get('market_cap', 0) or 0
        volume_change = current_volume - week_volume
        volume_change_pct = (volume_change / week_volume * 100) if week_volume > 0 else 0
        volume_change_sign = '+' if volume_change > 0 else ''
        
        # Calculate performance periods
        performance_1d = self._calculate_cumulative_performance(df, 1)
        performance_3d = self._calculate_cumulative_performance(df, 3)
        performance_7d = self._calculate_cumulative_performance(df, 7)
        
        # Calculate additional indicators
        volatility = self._calculate_volatility(df)
        sharpe_ratio = self._calculate_sharpe_ratio(df)
        positive_days_5 = self._calculate_positive_days(df, 5)
        
        return {
            'investor_count': int(current_investors) if current_investors > 0 else 'N/A',
            'investor_change_week': f"{investor_change_sign}{int(investor_change)}" if investor_change != 0 else "0",
            'volume': self._format_number(current_volume) if current_volume > 0 else 'N/A',
            'volume_change_week': f"{volume_change_sign}{self._format_number(volume_change)} ({volume_change_sign}{volume_change_pct:.1f}%)" if volume_change != 0 else "0 (0.0%)",
            'performance_1d': performance_1d,
            'performance_3d': performance_3d,
            'performance_7d': performance_7d,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'positive_days_5': positive_days_5,
            'investor_growth_week': ((current_investors - week_investors) / week_investors * 100) if week_investors > 0 else 0,
            'volume_increase_daily': volume_change_pct
        }
    
    def _calculate_cumulative_performance(self, df: pd.DataFrame, days: int) -> float:
        """Calculate cumulative performance over specified days"""
        if df.empty or len(df) < days:
            return 0.0
        
        try:
            # Get the last 'days' worth of percentage changes
            recent_pct = df.tail(days)['pct'].dropna()
            if recent_pct.empty:
                return 0.0
            
            # Calculate cumulative return: (1 + pct/100) compounded
            cumulative = ((1 + recent_pct / 100.0).prod() - 1) * 100.0
            return round(cumulative, 2)
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate 20-day volatility"""
        if len(df) < 20:
            return 0.0
        
        recent_returns = df.tail(20)['pct'].dropna()
        return round(recent_returns.std(), 2) if len(recent_returns) > 0 else 0.0
    
    def _calculate_sharpe_ratio(self, df: pd.DataFrame) -> float:
        """Calculate simple Sharpe-like ratio"""
        if len(df) < 20:
            return 0.0
        
        recent_returns = df.tail(20)['pct'].dropna()
        if len(recent_returns) == 0:
            return 0.0
        
        avg_return = recent_returns.mean()
        volatility = recent_returns.std()
        
        if volatility > 0:
            return round(avg_return / volatility, 2)
        return 0.0
    
    def _calculate_positive_days(self, df: pd.DataFrame, days: int) -> int:
        """Calculate number of positive days in last N days"""
        if len(df) < days:
            return 0
        
        recent_changes = df.tail(days)['pct'].dropna()
        return int((recent_changes > 0).sum()) if len(recent_changes) > 0 else 0
    
    def _format_number(self, num: float) -> str:
        """Format numbers for display"""
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"
    
    def should_analyze_fund(self, df: pd.DataFrame, fund_code: str, portfolio_funds: List[str]) -> bool:
        """
        Determine if a fund should be analyzed based on filters
        """
        # Check minimum history requirement
        if len(df) < config.filters.min_history_days:
            return False
        
        # Portfolio funds are always analyzed
        if fund_code in portfolio_funds:
            return True
        
        # Check investor count filter
        if not df.empty:
            latest_data = df.iloc[-1]
            current_investors = latest_data.get('number_of_investors', 0) or 0
            
            if current_investors < config.filters.min_investors:
                return False
        
        return True
    
    def get_latest_investor_count(self, df: pd.DataFrame) -> int:
        """Get the latest investor count from dataframe"""
        if df.empty:
            return 0
        
        latest_data = df.iloc[-1]
        return latest_data.get('number_of_investors', 0) or 0
    
    def extract_fund_company(self, fund_title: str) -> str:
        """
        Extract fund company name from title
        """
        if pd.isna(fund_title):
            return 'Bilinmeyen'
        
        title = fund_title.upper()
        
        # Yaygın şirket adları (uzundan kısaya sıralı - daha spesifik eşleşmeler önce)
        companies = [
            ('AK PORTFÖY', 'AK PORTFÖY'),
            ('AK PORTFOYü', 'AK PORTFÖY'), 
            ('AK PORTFOLIO', 'AK PORTFÖY'),
            ('İŞ PORTFÖY', 'İŞ PORTFÖY'),
            ('IS PORTFOLIO', 'İŞ PORTFÖY'),
            ('İS PORTFOLIO', 'İŞ PORTFÖY'),
            ('YAPI KREDI PORTFÖY', 'YAPI KREDİ'),
            ('YKB PORTFOY', 'YAPI KREDİ'),
            ('YAPI KREDI', 'YAPI KREDİ'),
            ('GARANTİ PORTFÖY', 'GARANTİ'),
            ('GARANTI PORTFOLIO', 'GARANTİ'),
            ('GARANTİ', 'GARANTİ'),
            ('ENPARA PORTFÖY', 'ENPARA'),
            ('ENPARA', 'ENPARA'),
            ('TEB PORTFÖY', 'TEB'),
            ('TEB PORTFOLIO', 'TEB'),
            ('FINANS PORTFÖY', 'FİNANS PORTFÖY'),
            ('FINANS PORTFOLIO', 'FİNANS PORTFÖY'),
            ('ZIRAAT PORTFÖY', 'ZİRAAT'),
            ('ZIRAAT PORTFOLIO', 'ZİRAAT'),
            ('HALKBANK PORTFÖY', 'HALKBANK'),
            ('HALK PORTFOY', 'HALKBANK'),
            ('HALK PORTFOLIO', 'HALKBANK'),
            ('VAKIF PORTFÖY', 'VAKIFbank'),
            ('VAKIFBANK PORTFOY', 'VAKIFbank'),
            ('VAKIF PORTFOLIO', 'VAKIFbank'),
            ('VAKIFBANK', 'VAKIFbank'),
            ('DENIZBANK PORTFÖY', 'DENİZBANK'),
            ('DENIZ PORTFOLIO', 'DENİZBANK'),
            ('DENIZBANK', 'DENİZBANK'),
            ('ALBARAKA PORTFÖY', 'ALBARAKA'),
            ('ALBARAKA PORTFOLIO', 'ALBARAKA'),
            ('QNB FINANS PORTFÖY', 'QNB FİNANS'),
            ('QNB PORTFOY', 'QNB FİNANS'),
            ('QNB PORTFOLIO', 'QNB FİNANS'),
            ('QNB', 'QNB FİNANS'),
            ('ALTERNATIF BANK PORTFÖY', 'ALTERNATİFBANK'),
            ('ALTERNATIF PORTFOY', 'ALTERNATİFBANK'),
            ('ALTERNATIF', 'ALTERNATİFBANK'),
            ('ANADOLU HAYAT EMEKLILIK PORTFÖY', 'ANADOLU HAYAT'),
            ('ANADOLU PORTFOY', 'ANADOLU HAYAT'),
            ('ANADOLU', 'ANADOLU HAYAT'),
            ('OYAK PORTFÖY', 'OYAK'),
            ('OYAK PORTFOLIO', 'OYAK'),
            ('ARTI PORTFÖY', 'ARTI'),
            ('ARTI PORTFOLIO', 'ARTI'),
            ('BIZIM PORTFÖY', 'BİZİM'),
            ('BIZIM PORTFOLIO', 'BİZİM'),
            ('MARMARA CAPITAL PORTFÖY', 'MARMARA CAPİTAL'),
            ('MARMARA PORTFOY', 'MARMARA CAPİTAL'),
            ('MARMARA', 'MARMARA CAPİTAL'),
            ('ICBC TURKEY PORTFÖY', 'ICBC TURKEY'),
            ('ICBC PORTFOY', 'ICBC TURKEY'),
            ('ICBC', 'ICBC TURKEY'),
            ('TURKISH INVESTMENT PORTFÖY', 'TURKISH INVESTMENT'),
            ('TURKISH PORTFOY', 'TURKISH INVESTMENT'),
            ('TURKISH', 'TURKISH INVESTMENT'),
            ('ATLAS PORTFÖY', 'ATLAS'),
            ('ATLAS PORTFOLIO', 'ATLAS'),
            ('ATA ASSET MANAGEMENT', 'ATA ASSET MANAGEMENT'),
            ('ATA PORTFOY', 'ATA'),
            ('İSTANBUL ASSET MANAGEMENT', 'İSTANBUL ASSET MANAGEMENT'),
            ('ISTANBUL ASSET MANAGEMENT', 'İSTANBUL ASSET MANAGEMENT'),
            ('İSTANBUL PORTFÖY', 'İSTANBUL PORTFÖY'),
            ('ALLBATROSS PORTFÖY', 'ALLBATROSS'),
            ('ALLBATROSS', 'ALLBATROSS')
        ]
        
        # Şirket adını bul
        for pattern, company_name in companies:
            if pattern in title:
                return company_name
        
        # Şirket bulunamazsa ilk iki kelimeyi al
        words = title.split()
        if len(words) >= 2:
            return f'{words[0]} {words[1]}'
        elif len(words) == 1:
            return words[0]
        
        return 'Bilinmeyen'
    
    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()
        logger.info("Data cache cleared")


if __name__ == "__main__":
    # Test data provider
    provider = FundDataProvider()
    
    # Test getting fund codes
    codes = provider.get_fund_codes()
    print(f"Found {len(codes)} fund codes")
    
    if codes:
        # Test getting fund data
        test_code = codes[0]
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=30)).isoformat()
        
        df = provider.get_fund_data(test_code, start_date, end_date)
        print(f"Fund {test_code}: {len(df)} days of data")
        
        if not df.empty:
            stats = provider.get_fund_statistics(df)
            print(f"Stats: {stats}")