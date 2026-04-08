#!/usr/bin/env python3
"""
Panel Manager Module
Manages panel data (JSON file operations), candidate tracking, and portfolio management
"""

import json
import os
from datetime import date
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from config import config
from technical_analyzer import CandidateResult


class PanelManager:
    """Manages panel data and portfolio operations"""
    
    def __init__(self, json_file: str = None):
        self.json_file = json_file or config.files.panel_json_file
        self.panel_data = self._load_panel_data()
    
    def _load_panel_data(self) -> Dict[str, Any]:
        """Load panel data from JSON file"""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📄 Panel verisi yüklendi: {self.json_file}")
                    return data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️ Panel dosyası okuma hatası: {e}")
                return self._create_default_panel()
        else:
            print("⚙️ İlk kurulum: panel dosyası oluşturuluyor...")
            return self._create_default_panel()
    
    def _create_default_panel(self) -> Dict[str, Any]:
        """Create default panel structure"""
        print("📝 Portföyünüzü eklemek için tefas_panel.json dosyasındaki 'portfolio_funds' listesini düzenleyin.")
        print("📋 Örnek: [\"DFI\", \"TLY\", \"YBS\", \"ZPX\"]")
        
        default_data = {
            "portfolio_funds": config.get_default_portfolio_funds(),
            "early_momentum_candidates": [],
            "trend_candidates": [],
            "last_updated": date.today().isoformat(),
            "tracking_settings": config.get_panel_settings(),
            "_info": {
                "description": "TEFAS Günlük Takip Paneli - Konfigürasyon Dosyası",
                "portfolio_funds_example": ["DFI", "TLY"],
                "last_modified": date.today().isoformat(),
                "version": "2.0-OOP"
            }
        }
        
        self.save_panel_data(default_data)
        return default_data
    
    def save_panel_data(self, data: Dict[str, Any] = None):
        """Save panel data to JSON file"""
        if data is None:
            data = self.panel_data
        
        data["last_updated"] = date.today().isoformat()
        data["_info"]["last_modified"] = date.today().isoformat()
        
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Panel verisi kaydedildi: {self.json_file}")
        except Exception as e:
            print(f"❌ Panel verisi kaydetme hatası: {e}")
    
    def get_panel_data(self) -> Dict[str, Any]:
        """Get complete panel data"""
        return self.panel_data
    
    def get_portfolio_funds(self) -> List[str]:
        """Get portfolio fund codes"""
        return self.panel_data.get("portfolio_funds", [])
    
    def add_portfolio_fund(self, fund_code: str):
        """Add a fund to portfolio"""
        portfolio = self.get_portfolio_funds()
        if fund_code not in portfolio:
            portfolio.append(fund_code)
            self.panel_data["portfolio_funds"] = portfolio
            self.save_panel_data()
            print(f"✅ {fund_code} portföye eklendi")
        else:
            print(f"⚠️ {fund_code} zaten portföyde mevcut")
    
    def remove_portfolio_fund(self, fund_code: str):
        """Remove a fund from portfolio"""
        portfolio = self.get_portfolio_funds()
        if fund_code in portfolio:
            portfolio.remove(fund_code)
            self.panel_data["portfolio_funds"] = portfolio
            self.save_panel_data()
            print(f"✅ {fund_code} portföyden çıkarıldı")
        else:
            print(f"⚠️ {fund_code} portföyde bulunamadı")
    
    def update_candidates(self, early_momentum: List[CandidateResult], trend_candidates: List[CandidateResult]):
        """Update candidate lists"""
        # Clear existing candidates
        self.panel_data["early_momentum_candidates"] = []
        self.panel_data["trend_candidates"] = []
        
        # Add new early momentum candidates
        for candidate in early_momentum:
            self.panel_data["early_momentum_candidates"].append({
                "code": candidate.fund_code,
                "company": candidate.company,
                "score": candidate.score,
                "criteria": candidate.criteria,
                "rsi": candidate.rsi,
                "macd": candidate.macd,
                "macd_signal": candidate.macd_signal,
                "price": candidate.price,
                "added_date": date.today().isoformat(),
                "fund_statistics": candidate.fund_statistics
            })
        
        # Add new trend candidates
        for candidate in trend_candidates:
            self.panel_data["trend_candidates"].append({
                "code": candidate.fund_code,
                "company": candidate.company,
                "score": candidate.score,
                "criteria": candidate.criteria,
                "rsi": candidate.rsi,
                "macd": candidate.macd,
                "macd_signal": candidate.macd_signal,
                "price": candidate.price,
                "added_date": date.today().isoformat(),
                "fund_statistics": candidate.fund_statistics
            })
        
        self.save_panel_data()
        print(f"📈 Adaylar güncellendi: {len(early_momentum)} erken momentum, {len(trend_candidates)} trend adayı")
    
    def get_early_momentum_candidates(self) -> List[Dict[str, Any]]:
        """Get early momentum candidates"""
        return self.panel_data.get("early_momentum_candidates", [])
    
    def get_trend_candidates(self) -> List[Dict[str, Any]]:
        """Get trend candidates"""
        return self.panel_data.get("trend_candidates", [])
    
    def get_tracking_settings(self) -> Dict[str, Any]:
        """Get tracking settings"""
        return self.panel_data.get("tracking_settings", config.get_panel_settings())
    
    def update_tracking_settings(self, settings: Dict[str, Any]):
        """Update tracking settings"""
        current_settings = self.get_tracking_settings()
        current_settings.update(settings)
        self.panel_data["tracking_settings"] = current_settings
        self.save_panel_data()
    
    def get_panel_summary(self) -> Dict[str, int]:
        """Get panel summary statistics"""
        return {
            "portfolio_funds": len(self.get_portfolio_funds()),
            "early_momentum_candidates": len(self.get_early_momentum_candidates()),
            "trend_candidates": len(self.get_trend_candidates()),
            "last_updated": self.panel_data.get("last_updated", "Unknown")
        }
    
    def clean_old_candidates(self, days_to_keep: int = 7):
        """Clean candidates older than specified days"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Filter early momentum candidates
        early_filtered = []
        for candidate in self.get_early_momentum_candidates():
            added_date_str = candidate.get("added_date", "")
            try:
                added_date = datetime.fromisoformat(added_date_str)
                if added_date >= cutoff_date:
                    early_filtered.append(candidate)
            except (ValueError, TypeError):
                # Keep candidates with invalid dates
                early_filtered.append(candidate)
        
        # Filter trend candidates
        trend_filtered = []
        for candidate in self.get_trend_candidates():
            added_date_str = candidate.get("added_date", "")
            try:
                added_date = datetime.fromisoformat(added_date_str)
                if added_date >= cutoff_date:
                    trend_filtered.append(candidate)
            except (ValueError, TypeError):
                # Keep candidates with invalid dates
                trend_filtered.append(candidate)
        
        # Update if any changes
        old_early_count = len(self.get_early_momentum_candidates())
        old_trend_count = len(self.get_trend_candidates())
        
        self.panel_data["early_momentum_candidates"] = early_filtered
        self.panel_data["trend_candidates"] = trend_filtered
        
        removed_early = old_early_count - len(early_filtered)
        removed_trend = old_trend_count - len(trend_filtered)
        
        if removed_early > 0 or removed_trend > 0:
            self.save_panel_data()
            print(f"🧹 Eski adaylar temizlendi: {removed_early} erken momentum, {removed_trend} trend adayı")
    
    def export_panel_backup(self, backup_file: str = None) -> str:
        """Export panel data as backup"""
        if backup_file is None:
            timestamp = date.today().strftime("%Y%m%d")
            backup_file = f"tefas_panel_backup_{timestamp}.json"
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.panel_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Panel yedeklendi: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Yedekleme hatası: {e}")
            return ""
    
    def import_panel_backup(self, backup_file: str) -> bool:
        """Import panel data from backup"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validate basic structure
            required_keys = ["portfolio_funds", "early_momentum_candidates", "trend_candidates"]
            if all(key in backup_data for key in required_keys):
                self.panel_data = backup_data
                self.save_panel_data()
                print(f"✅ Panel yedeklemesi geri yüklendi: {backup_file}")
                return True
            else:
                print(f"❌ Geçersiz yedekleme dosyası: {backup_file}")
                return False
        except Exception as e:
            print(f"❌ Yedekleme geri yükleme hatası: {e}")
            return False
    
    def get_portfolio_analysis_template(self) -> List[Dict[str, Any]]:
        """Get template for portfolio analysis"""
        portfolio_funds = self.get_portfolio_funds()
        template = []
        
        for fund_code in portfolio_funds:
            template.append({
                "Fon": fund_code,
                "Trend_Status": "➡️ Durağan/Kararsız",
                "Yükseliş_Skor": 0.0,
                "Düşüş_Skor": 0.0,
                "Kriterler": "Veri bekleniyor",
                "RSI": "N/A",
                "MACD": "N/A",
                "Signal": "N/A",
                "Fiyat": "N/A",
                "Yatırımcı": "N/A",
                "Yatırımcı_Değişim": "N/A",
                "Hacim": "N/A",
                "Hacim_Değişim": "N/A"
            })
        
        return template
    
    def print_panel_info(self):
        """Print panel information"""
        summary = self.get_panel_summary()
        print("\n📊 Panel Durumu:")
        print(f"   💼 Portföy Fonları: {summary['portfolio_funds']}")
        print(f"   🚀 Erken Momentum: {summary['early_momentum_candidates']}")
        print(f"   💎 Trend Adayları: {summary['trend_candidates']}")
        print(f"   📅 Son Güncelleme: {summary['last_updated']}")


if __name__ == "__main__":
    # Test panel manager
    panel = PanelManager()
    
    # Print current state
    panel.print_panel_info()
    
    # Test portfolio operations
    portfolio = panel.get_portfolio_funds()
    print(f"Current portfolio: {portfolio}")
    
    # Test summary
    summary = panel.get_panel_summary()
    print(f"Panel summary: {summary}")