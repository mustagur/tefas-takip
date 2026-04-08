#!/usr/bin/env python3
"""
TEFAS Configuration Module
Manages all configuration parameters and settings
"""

from dataclasses import dataclass
from typing import Optional, List
import os


@dataclass
class TechnicalAnalysisConfig:
    """Enhanced technical analysis parameters with 100-point scoring system"""
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bollinger_period: int = 20
    bollinger_std: int = 2
    
    # New 100-point scoring system
    # Trend Component (Max 40 points)
    rsi_strong_score: int = 10      # RSI > 60
    macd_score: int = 20           # MACD positive crossover
    bollinger_score: int = 10      # Bollinger breakout
    
    # Investor Flow Component (Max 20 points) 
    investor_flow_score: int = 20  # 7-day investor growth >3% + AUM increase
    
    # Volume & Liquidity Component (Max 20 points)
    volume_liquidity_score: int = 20  # Daily volume increase + 5-day avg rising
    
    # Volatility Component (Max 20 points)
    volatility_score: int = 20     # Low ATR increase + Sharpe > 1
    
    # Timing Component (Max 10 points) 
    timing_score: int = 10         # 4 out of 5 positive closes
    
    # Legacy scores for backward compatibility
    rsi_early_score: int = 5       # For transitional period
    
    # RSI thresholds
    rsi_early_min: float = 55.0
    rsi_early_max: float = 60.0
    rsi_strong_min: float = 60.0
    rsi_decline_max: float = 40.0


@dataclass
class FilterConfig:
    """Data filtering parameters"""
    min_investors: int = 50
    min_history_days: int = 25
    exclude_portfolio_from_filter: bool = True


@dataclass
class AnalysisConfig:
    """Analysis parameters"""
    history_days: int = 45
    end_offset_days: int = 0
    sleep_between: float = 0.05
    retry_limit: int = 3
    max_codes: Optional[int] = None  # Set to small number for testing
    min_investors: int = 50
    
    # Case analysis thresholds
    case1_streak_days: int = 3
    case1_min_daily: float = 1.0
    case2_window_days: int = 3
    case2_min_cum: float = 4.0
    case3_window_days: int = 5
    case3_min_cum: float = 5.0
    
    # New candidate thresholds for 100-point system
    early_momentum_min_score: int = 50   # 50-75 range for early momentum
    early_momentum_max_score: int = 75
    trend_min_score: int = 75            # 75+ for trend candidates


@dataclass
class FileConfig:
    """File and path configurations"""
    data_dir: str = "."
    panel_json_file: str = "tefas_panel.json"
    html_report_file: str = "tefas_report.html"
    excel_report_prefix: str = "tefas_report"
    excel_report_extension: str = ".xlsx"


@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_name: str = "TEFAS Reports Bot"
    
    @property
    def smtp_user(self) -> Optional[str]:
        return os.getenv('SMTP_USER')
    
    @property
    def smtp_password(self) -> Optional[str]:
        return os.getenv('SMTP_PASSWORD')
    
    @property
    def recipient_email(self) -> Optional[str]:
        return os.getenv('RECIPIENT_EMAIL')
    
    @property
    def is_configured(self) -> bool:
        return all([self.smtp_user, self.smtp_password, self.recipient_email])


class TefasConfig:
    """Main configuration class that combines all configs"""
    
    def __init__(self):
        self.technical = TechnicalAnalysisConfig()
        self.filters = FilterConfig()
        self.analysis = AnalysisConfig()
        self.files = FileConfig()
        self.email = EmailConfig()
    
    def get_default_portfolio_funds(self) -> List[str]:
        """Default portfolio funds"""
        return ["DFI", "TLY"]
    
    def get_panel_settings(self) -> dict:
        """Default panel settings"""
        return {
            "early_momentum_min_score": self.analysis.early_momentum_min_score,
            "trend_min_score": self.analysis.trend_min_score,
            "portfolio_alert_threshold": 1.5
        }
    
    def print_summary(self):
        """Print configuration summary"""
        print("🔧 TEFAS Configuration Summary:")
        print(f"   📊 Technical Analysis: RSI({self.technical.rsi_period}), MACD({self.technical.macd_fast},{self.technical.macd_slow},{self.technical.macd_signal})")
        print(f"   📏 Filters: Min {self.filters.min_investors} investors, {self.filters.min_history_days} days history")
        print(f"   🎯 Analysis: {self.analysis.history_days} days window, {self.analysis.max_codes or 'All'} funds")
        print(f"   📧 Email: {'✅ Configured' if self.email.is_configured else '❌ Not configured'}")
        print(f"   📁 Files: Panel({self.files.panel_json_file}), Report({self.files.html_report_file})")


# Global configuration instance
config = TefasConfig()


if __name__ == "__main__":
    # Test configuration
    config.print_summary()