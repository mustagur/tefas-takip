#!/usr/bin/env python3
"""
TEFAS Trend Analysis - Object-Oriented Version
Version: OOP 2.0

Main Script for running TEFAS fund analysis with modular OOP architecture
"""

import time
from datetime import datetime
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


# ========= PANEL FONKSİYONLARI =========
def load_panel_data():
    """Panel JSON dosyasını yükler"""
    if os.path.exists(PANEL_JSON_FILE):
        with open(PANEL_JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Varsayılan ayarlar - İlk kurulum için boş portföy
        print("⚙️  İlk kurulum: tefas_panel.json oluşturuluyor...")
        print("📝 Portföyünüzü eklemek için tefas_panel.json dosyasındaki 'portfolio_funds' listesini düzenleyin.")
        print("📋 Örnek: [\"DFI\", \"TLY\", \"YBS\", \"ZPX\"]")
        
        default_data = {
            "portfolio_funds": [],
            "early_momentum_candidates": [],
            "trend_candidates": [],
            "last_updated": date.today().isoformat(),
            "tracking_settings": {
                "early_momentum_min_score": 1.5,
                "trend_min_score": 3.0,
                "portfolio_alert_threshold": 1.5
            },
            "_info": {
                "description": "TEFAS Günlük Takip Paneli - Konfigürasyon Dosyası",
                "portfolio_funds_example": ["DFI", "TLY"],
                "last_modified": date.today().isoformat()
            }
        }
        save_panel_data(default_data)
        return default_data

def save_panel_data(data):
    """Panel JSON dosyasını kaydeder"""
    data["last_updated"] = date.today().isoformat()
    with open(PANEL_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_candidates(panel_data, early_momentum, trend_candidates):
    """Aday listelerini günceller"""
    # Mevcut adayları temizle
    panel_data["early_momentum_candidates"] = []
    panel_data["trend_candidates"] = []
    
    # Yeni adayları ekle
    for candidate in early_momentum:
        panel_data["early_momentum_candidates"].append({
            "code": candidate["Fon"],
            "score": candidate["Skor"],
            "criteria": candidate["Kriterler"],
            "rsi": candidate["RSI"],
            "added_date": date.today().isoformat()
        })
    
    for candidate in trend_candidates:
        panel_data["trend_candidates"].append({
            "code": candidate["Fon"],
            "score": candidate["Skor"],
            "criteria": candidate["Kriterler"],
            "rsi": candidate["RSI"],
            "added_date": date.today().isoformat()
        })
    
    save_panel_data(panel_data)

def generate_html_report(panel_data, portfolio_analysis, early_momentum, trend_candidates, declining_rows, case1_rows, case2_rows, case3_rows):
    """HTML rapor oluşturur"""
    from datetime import datetime
    
    html_content = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TEFAS Günlük Takip Paneli</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f7; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center; }}
        .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .fund-card {{ border: 1px solid #e1e5e9; border-radius: 8px; padding: 20px; margin-bottom: 15px; background: #fafbfc; }}
        .trend-up {{ border-left: 4px solid #28a745; }}
        .trend-down {{ border-left: 4px solid #dc3545; }}
        .trend-neutral {{ border-left: 4px solid #ffc107; }}
        .metric {{ display: inline-block; margin-right: 20px; }}
        .metric-label {{ font-weight: 600; color: #495057; }}
        .metric-value {{ color: #212529; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .summary-number {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .candidate-item {{ background: #f8f9fa; padding: 15px; margin-bottom: 10px; border-radius: 6px; border-left: 3px solid #007bff; }}
        h1, h2 {{ margin-top: 0; }}
        .timestamp {{ opacity: 0.7; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 TEFAS Günlük Takip Paneli</h1>
            <p class="timestamp">Güncelleme: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Son Kaydetme: {panel_data.get('last_updated', 'Bilinmiyor')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="summary-number">{len(panel_data.get('portfolio_funds', []))}</div>
                <div>Portföy Fonları</div>
            </div>
            <div class="summary-card">
                <div class="summary-number positive">{len(panel_data.get('early_momentum_candidates', []))}</div>
                <div>Erken Momentum</div>
            </div>
            <div class="summary-card">
                <div class="summary-number positive">{len(panel_data.get('trend_candidates', []))}</div>
                <div>Güçlü Trend</div>
            </div>
            <div class="summary-card">
                <div class="summary-number negative">{len(declining_rows) if declining_rows else 0}</div>
                <div>Aktif Uyarılar</div>
            </div>
        </div>
        
        <!-- Puanlama Sistemi Bilgilendirmesi -->
        <div class="section" style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border: 1px solid #dee2e6;">
            <h2>ℹ️ Puanlama Sistemi</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 20px;">
                <div>
                    <h3 style="color: #28a745; margin-bottom: 15px;">📈 YÜKSELİŞ PUANLARI</h3>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                        <li><strong>MACD Pozitif Kesişim:</strong> +2 puan (En güçlü sinyal)</li>
                        <li><strong>Bollinger Bandı Kırılım:</strong> +1 puan</li>
                        <li><strong>RSI 55-60 (Erken):</strong> +0.5 puan</li>
                        <li><strong>RSI 60+ (Güçlü):</strong> +1 puan</li>
                    </ul>
                </div>
                <div>
                    <h3 style="color: #dc3545; margin-bottom: 15px;">📉 DÜŞÜŞ PUANLARI</h3>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                        <li><strong>MACD Negatif Kesişim:</strong> +2 puan (Güçlü düşüş)</li>
                        <li><strong>Bollinger Altına Kırılım:</strong> +1 puan</li>
                        <li><strong>RSI 40'ın Altına Düşüş:</strong> +1 puan</li>
                    </ul>
                </div>
            </div>
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #ffc107;">
                <strong>🎯 Skor Aralıkları:</strong><br>
                • <strong>1.5-2.5 Puan:</strong> Erken Momentum Adayları (Dikkat Edilecek)<br>
                • <strong>3+ Puan:</strong> Güçlü Trend Adayları (Yüksek Sinyal Gücü)
            </div>
        </div>
"""
    
    # Portföy Durumu
    html_content += '<div class="section"><h2>💼 Portföy Durumu</h2>'
    if portfolio_analysis:
        for fund in portfolio_analysis:
            trend_class = "trend-neutral"
            if "🔥" in fund['Trend_Status'] or "📈" in fund['Trend_Status']:
                trend_class = "trend-up"
            elif "🔴" in fund['Trend_Status'] or "📉" in fund['Trend_Status']:
                trend_class = "trend-down"
            
            investor_str = f"{fund['Yatırımcı']:,}" if isinstance(fund['Yatırımcı'], int) else str(fund['Yatırımcı'])
            
            html_content += f"""
            <div class="fund-card {trend_class}">
                <h3>{fund['Fon']} | {fund['Trend_Status']}</h3>
                <div class="metric">
                    <span class="metric-label">RSI:</span> 
                    <span class="metric-value">{fund['RSI']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">MACD:</span> 
                    <span class="metric-value">{fund['MACD']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Fiyat:</span> 
                    <span class="metric-value">{fund['Fiyat']} TL</span>
                </div>
                <br>
                <div class="metric">
                    <span class="metric-label">Yatırımcı:</span> 
                    <span class="metric-value">{investor_str} kişi ({fund['Yatırımcı_Değişim']})</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Hacim:</span> 
                    <span class="metric-value">{fund['Hacim']} TL ({fund['Hacim_Değişim']})</span>
                </div>
                {f'<p><strong>Kriterler:</strong> {fund["Kriterler"]}</p>' if fund['Kriterler'] != "Belirgin trend sinyali yok" else ''}
            </div>
            """
    else:
        html_content += '<p>⚠️ Portföy fonları analiz edilemedi</p>'
    html_content += '</div>'
    
    # Erken Momentum Adayları - Detaylı bilgilerle
    html_content += '<div class="section"><h2>🚀 Erken Momentum Adayları</h2>'
    if early_momentum:
        for candidate in early_momentum:
            investor_str = f"{candidate['Yatırımcı']:,}" if isinstance(candidate['Yatırımcı'], int) else str(candidate['Yatırımcı'])
            
            html_content += f"""
            <div class="fund-card">
                <h3>{candidate['Fon']} | Skor: {candidate['Skor']}</h3>
                <div class="metric">
                    <span class="metric-label">RSI:</span> 
                    <span class="metric-value">{candidate['RSI']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">MACD:</span> 
                    <span class="metric-value">{candidate['MACD']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Fiyat:</span> 
                    <span class="metric-value">{candidate['Fiyat']} TL</span>
                </div>
                <br>
                <div class="metric">
                    <span class="metric-label">Yatırımcı:</span> 
                    <span class="metric-value">{investor_str} kişi ({candidate['Yatırımcı_Değişim']})</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Hacim:</span> 
                    <span class="metric-value">{candidate['Hacim']} TL ({candidate['Hacim_Değişim']})</span>
                </div>
                <p><strong>Kriterler:</strong> {candidate['Kriterler']}</p>
            </div>
            """
    else:
        html_content += '<p>🔍 Şu anda erken momentum adayı yok</p>'
    html_content += '</div>'
    
    # Trend Adayları - Detaylı bilgilerle
    html_content += '<div class="section"><h2>💪 Trend Adayları</h2>'
    if trend_candidates:
        for candidate in trend_candidates:
            investor_str = f"{candidate['Yatırımcı']:,}" if isinstance(candidate['Yatırımcı'], int) else str(candidate['Yatırımcı'])
            
            html_content += f"""
            <div class="fund-card">
                <h3>{candidate['Fon']} | Skor: {candidate['Skor']}</h3>
                <div class="metric">
                    <span class="metric-label">RSI:</span> 
                    <span class="metric-value">{candidate['RSI']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">MACD:</span> 
                    <span class="metric-value">{candidate['MACD']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Fiyat:</span> 
                    <span class="metric-value">{candidate['Fiyat']} TL</span>
                </div>
                <br>
                <div class="metric">
                    <span class="metric-label">Yatırımcı:</span> 
                    <span class="metric-value">{investor_str} kişi ({candidate['Yatırımcı_Değişim']})</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Hacim:</span> 
                    <span class="metric-value">{candidate['Hacim']} TL ({candidate['Hacim_Değişim']})</span>
                </div>
                <p><strong>Kriterler:</strong> {candidate['Kriterler']}</p>
            </div>
            """
    else:
        html_content += '<p>🔍 Şu anda güçlü trend adayı yok</p>'
    html_content += '</div>'
    
    # Uyarılar
    html_content += '<div class="section"><h2>⚠️ Uyarılar & Alerts</h2>'
    if declining_rows:
        html_content += f'<p><strong>🚨 PORTFÖY UYARISI:</strong> {len(declining_rows)} fonda düşüş sinyali!</p>'
        for fund in declining_rows:
            html_content += f'<div class="candidate-item" style="border-left-color: #dc3545;">🔴 <strong>{fund.get("Fon", fund.get("code", "Bilinmiyor"))}</strong>: {fund.get("Kriterler", fund.get("criteria", "Detay yok"))}</div>'
    else:
        html_content += '<p>✅ Portföyünüzde şu anda düşüş uyarısı yok</p>'
    html_content += '</div>'
    
    # Momentum Performans Bölümü
    html_content += '<div class="section"><h2>📊 Momentum & Performans Analizi</h2>'
    
    # 3 gün art arda performans
    if case1_rows:
        html_content += f'<h3>① 3 Gün Art Arda ≥ %1.0 ({len(case1_rows)} fon)</h3>'
        html_content += '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">'
        for fund in case1_rows:
            html_content += f'<span style="background: #e7f3ff; padding: 5px 10px; border-radius: 15px; font-weight: 500;">{fund["Fon"]}</span>'
        html_content += '</div>'
    else:
        html_content += '<h3>① 3 Gün Art Arda ≥ %1.0</h3><p>Kriterleri karşılayan fon bulunamadı</p>'
    
    # Son 3 gün toplam performans
    if case2_rows:
        html_content += f'<h3>② Son 3 Gün Toplam ≥ %4.0 ({len(case2_rows)} fon)</h3>'
        html_content += '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">'
        for fund in case2_rows:
            html_content += f'<span style="background: #ffe7f3; padding: 5px 10px; border-radius: 15px; font-weight: 500;">{fund["Fon"]}</span>'
        html_content += '</div>'
    else:
        html_content += '<h3>② Son 3 Gün Toplam ≥ %4.0</h3><p>Kriterleri karşılayan fon bulunamadı</p>'
    
    # Haftalık performans
    if case3_rows:
        html_content += f'<h3>③ Haftalık (5gün) Toplam ≥ %5.0 ({len(case3_rows)} fon)</h3>'
        html_content += '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">'
        for fund in case3_rows:
            html_content += f'<span style="background: #f0fff4; padding: 5px 10px; border-radius: 15px; font-weight: 500;">{fund["Fon"]}</span>'
        html_content += '</div>'
    else:
        html_content += '<h3>③ Haftalık (5gün) Toplam ≥ %5.0</h3><p>Kriterleri karşılayan fon bulunamadı</p>'
    
    html_content += '</div>'
    
    html_content += """
    </div>
</body>
</html>
    """
    
    # HTML dosyasını kaydet
    with open('tefas_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 HTML Rapor kaydedildi: tefas_report.html")
    print(f"🔍 Raporu görüntülemek için: open tefas_report.html")
    
    # Excel raporu da oluştur
    print(f"📊 Excel raporu hazırlanıyor... (EXCEL_AVAILABLE: {EXCEL_AVAILABLE})")
    if EXCEL_AVAILABLE:
        try:
            print(f"🛠️ Excel fonksiyonu çağırılıyor...")
            excel_filename = generate_excel_report_internal(panel_data, portfolio_analysis, early_momentum, trend_candidates, declining_rows, case1_rows, case2_rows, case3_rows)
            if excel_filename:
                print(f"✅ Hem HTML hem Excel raporu başarıyla oluşturuldu! ({excel_filename})")
            else:
                print(f"⚠️ Excel dosyası oluşmadı (None döndü)")
        except Exception as e:
            print(f"⚠️ Excel raporu oluşturulurken hata: {e}")
            import traceback
            traceback.print_exc()
            print(f"📄 HTML raporu kullanılabilir durumda.")
    else:
        print(f"⚠️ openpyxl kütüphanesi bulunamadı. Sadece HTML raporu oluşturuldu.")
        print(f"💾 Excel özelliği için: pip install openpyxl")

def print_daily_tracking_panel_with_cases(panel_data, portfolio_analysis, early_momentum, trend_candidates, declining_rows, case1_rows, case2_rows, case3_rows):
    """TEFAS Günlük Takip Paneli'ni gösterir ve HTML rapor oluşturur"""
    from datetime import datetime
    
    # HTML raporu oluştur
    generate_html_report(panel_data, portfolio_analysis, early_momentum, trend_candidates, declining_rows, case1_rows, case2_rows, case3_rows)
    print("\n" + "=" * 80)
    print("📈  TEFAS GÜNLÜK TAKİP PANELİ  📈")
    print("=" * 80)
    print(f"📅 Güncelleme Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📋 Son Kaydetme: {panel_data.get('last_updated', 'Bilinmiyor')}")
    
    # PORTFÖY DURUMU
    print("\n💼 PORTFÖY DURUMU")
    print("─" * 50)
    
    if portfolio_analysis:
        for fund in portfolio_analysis:
            # Trend durumuna göre ikon
            if "🔥" in fund['Trend_Status'] or "📈" in fund['Trend_Status']:
                trend_icon = "🔼"
            elif "🔴" in fund['Trend_Status'] or "📉" in fund['Trend_Status']:
                trend_icon = "🔽"
            else:
                trend_icon = "➡️"
            
            print(f"\n{fund['Fon']} | {trend_icon} {fund['Trend_Status']}")
            print(f"  📊 RSI: {fund['RSI']} | MACD: {fund['MACD']} | Fiyat: {fund['Fiyat']} TL")
            
            investor_str = f"{fund['Yatırımcı']:,}" if isinstance(fund['Yatırımcı'], int) else str(fund['Yatırımcı'])
            print(f"  👥 {investor_str} yatırımcı ({fund['Yatırımcı_Değişim']}) | 📊 {fund['Hacim']} TL ({fund['Hacim_Değişim']})")
            
            if fund['Kriterler'] != "Belirgin trend sinyali yok":
                print(f"  🎦 {fund['Kriterler']}")
    else:
        print("⚠️ Portföy fonları analiz edilemedi")
    
    # TAKİP LİSTESİ - ERKEN MOMENTUM
    print("\n\n🚀 TAKİP LİSTESİ - ERKEN MOMENTUM ADAYLARI")
    print("─" * 60)
    
    if panel_data.get('early_momentum_candidates'):
        for i, candidate in enumerate(panel_data['early_momentum_candidates'], 1):
            print(f"{i}. {candidate['code']} (Skor: {candidate['score']})")
            print(f"   📊 RSI: {candidate['rsi']} | Ekleme: {candidate['added_date']}")
            print(f"   🎦 {candidate['criteria']}")
    else:
        print("🔍 Şu anda erken momentum adayı yok")
    
    # TAKİP LİSTESİ - TREND ADAYLARI
    print("\n\n💪 TAKİP LİSTESİ - TREND ADAYLARI")
    print("─" * 60)
    
    if panel_data.get('trend_candidates'):
        for i, candidate in enumerate(panel_data['trend_candidates'], 1):
            print(f"{i}. {candidate['code']} (Skor: {candidate['score']})")
            print(f"   📊 RSI: {candidate['rsi']} | Ekleme: {candidate['added_date']}")
            print(f"   🎦 {candidate['criteria']}")
    else:
        print("🔍 Şu anda güçlü trend adayı yok")
    
    # UYARILAR
    print("\n\n⚠️ UYARILAR & ALERTS")
    print("─" * 40)
    
    if declining_rows:
        print(f"🚨 PORTFÖY UYARISI: {len(declining_rows)} fonda düşüş sinyali!")
        for fund in declining_rows:
            print(f"  🔴 {fund.get('Fon', fund.get('code', 'Bilinmiyor'))}: {fund.get('Kriterler', fund.get('criteria', 'Detay yok'))}")
    else:
        print("✅ Portföyünüzde şu anda düşüş uyarısı yok")
    
    # ÖZET
    print("\n\n📈 ÖZET DURUM")
    print("─" * 30)
    
    portfolio_count = len(panel_data.get('portfolio_funds', []))
    early_count = len(panel_data.get('early_momentum_candidates', []))
    trend_count = len(panel_data.get('trend_candidates', []))
    alert_count = len(declining_rows) if declining_rows else 0
    
    print(f"💼 Portföy Fonları      : {portfolio_count} fon")
    print(f"🚀 Erken Momentum     : {early_count} aday")
    print(f"💪 Güçlü Trend        : {trend_count} aday")
    print(f"⚠️  Aktif Uyarılar     : {alert_count} uyarı")
    
    print("\n" + "=" * 80)
    print("🎆 Panel güncellendi! Bir sonraki çalıştırmada otomatik olarak takip devam edecek.")
    print("=" * 80)


# ========= EXCEL RAPOR FONKSİYONU =========
def generate_excel_report_internal(panel_data, portfolio_analysis, early_momentum, trend_candidates, declining_rows, case1_rows, case2_rows, case3_rows):
    """Profesyonel Excel raporu oluşturur (Dahili entegrasyon)"""
    from datetime import datetime
    
    if not EXCEL_AVAILABLE:
        print("⚠️ Excel raporu için openpyxl gerekli: pip install openpyxl")
        return None
    
    # Workbook ve stilleri hazırla
    wb = Workbook()
    
    # Stil tanımlamaları
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4472C4")
    subheader_font = Font(bold=True, color="2F5597")
    center_alignment = Alignment(horizontal="center", vertical="center")
    wrap_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )
    
    # Renk kodları
    green_fill = PatternFill("solid", fgColor="E8F5E8")
    red_fill = PatternFill("solid", fgColor="FFEBEE")
    yellow_fill = PatternFill("solid", fgColor="FFF9C4")
    gold_fill = PatternFill("solid", fgColor="FFF8DC")
    
    # 1. ÖZET SHEET
    ws_summary = wb.active
    ws_summary.title = "📊 Özet"
    
    # Başlık
    ws_summary.merge_cells('A1:E1')
    ws_summary['A1'] = f"TEFAS Günlük Takip Paneli - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws_summary['A1'].font = Font(bold=True, size=16, color="2F5597")
    ws_summary['A1'].alignment = center_alignment
    
    # Özet kartları
    summary_data = [
        ["Kategori", "Adet", "Durum"],
        ["💼 Portföy Fonları", len(panel_data.get('portfolio_funds', [])), "Aktif"],
        ["🚀 Erken Momentum", len(panel_data.get('early_momentum_candidates', [])), "İzlemede"],
        ["💪 Güçlü Trend", len(panel_data.get('trend_candidates', [])), "İzlemede"],
        ["⚠️ Aktif Uyarılar", len(declining_rows) if declining_rows else 0, "Dikkat"]
    ]
    
    for row_idx, row_data in enumerate(summary_data, 3):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border
            if row_idx == 3:  # Header row
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment
            else:
                cell.alignment = center_alignment
    
    # Email bilgisi ekle
    email_info_font = Font(size=10, italic=True, color="666666")
    
    # Email bilgisini ekle
    row = 9  # Özet tablosunun altına
    ws_summary[f'A{row}'] = "📧 Email Raporu:"
    ws_summary[f'A{row}'].font = Font(bold=True)
    
    ws_summary[f'B{row}'] = "Bu rapor melihekmekci1@gmail.com adresine gönderilmiştir"
    ws_summary[f'B{row}'].font = email_info_font
    
    # Açıklama ekle
    ws_summary[f'A{row+1}'] = "📅 Her iş günü saat 09:30'da otomatik olarak güncellenir."
    ws_summary[f'A{row+1}'].font = Font(size=9, italic=True)
    ws_summary.merge_cells(f'A{row+1}:C{row+1}')
    
    # Sütun genişlikleri
    ws_summary.column_dimensions['A'].width = 25
    ws_summary.column_dimensions['B'].width = 30
    ws_summary.column_dimensions['C'].width = 15
    
    # 2. PORTFÖY SHEET
    if portfolio_analysis:
        ws_portfolio = wb.create_sheet(title="💼 Portföy")
        
        # Başlıklar
        headers = ["Fon Kodu", "Trend Durumu", "RSI", "MACD", "Fiyat (TL)", 
                  "Yatırımcı", "Yatırımcı Değişim", "Hacim", "Hacim Değişim", "Kriterler"]
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws_portfolio.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
            cell.border = thin_border
        
        # Veri satırları
        for row_idx, fund in enumerate(portfolio_analysis, 2):
            data = [
                fund['Fon'],
                fund['Trend_Status'],
                fund['RSI'],
                fund['MACD'],
                fund['Fiyat'],
                fund['Yatırımcı'],
                fund['Yatırımcı_Değişim'],
                fund['Hacim'],
                fund['Hacim_Değişim'],
                fund['Kriterler']
            ]
            
            for col_idx, value in enumerate(data, 1):
                cell = ws_portfolio.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                
                # Trend durumuna göre renklendirme
                if col_idx == 2:  # Trend Status sütunu
                    if "🔥" in str(value) or "📈" in str(value):
                        cell.fill = green_fill
                    elif "🔴" in str(value) or "📉" in str(value):
                        cell.fill = red_fill
                    else:
                        cell.fill = yellow_fill
                
                # Hizalama
                if col_idx in [3, 4, 5]:  # RSI, MACD, Fiyat
                    cell.alignment = center_alignment
                elif col_idx == 10:  # Kriterler
                    cell.alignment = wrap_alignment
        
        # Sütun genişlikleri
        column_widths = [12, 20, 8, 12, 12, 12, 15, 15, 20, 40]
        for idx, width in enumerate(column_widths, 1):
            ws_portfolio.column_dimensions[chr(64 + idx)].width = width
    
    # 3. ERKEN MOMENTUM SHEET
    if early_momentum:
        ws_early = wb.create_sheet(title="🚀 Erken Momentum")
        
        headers = ["Fon Kodu", "Skor", "RSI", "MACD", "Fiyat (TL)", 
                  "Yatırımcı", "Hacim", "Kriterler"]
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws_early.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
            cell.border = thin_border
        
        for row_idx, candidate in enumerate(early_momentum, 2):
            data = [
                candidate['Fon'],
                candidate['Skor'],
                candidate['RSI'],
                candidate['MACD'],
                candidate['Fiyat'],
                candidate['Yatırımcı'],
                candidate['Hacim'],
                candidate['Kriterler']
            ]
            
            for col_idx, value in enumerate(data, 1):
                cell = ws_early.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                if col_idx == 8:  # Kriterler
                    cell.alignment = wrap_alignment
                elif col_idx in [2, 3, 4, 5]:  # Skor, RSI, MACD, Fiyat
                    cell.alignment = center_alignment
        
        # Sütun genişlikleri
        column_widths = [12, 8, 8, 12, 12, 12, 15, 40]
        for idx, width in enumerate(column_widths, 1):
            ws_early.column_dimensions[chr(64 + idx)].width = width
    
    # 4. TREND ADAYLARI SHEET
    if trend_candidates:
        ws_trend = wb.create_sheet(title="💪 Trend Adayları")
        
        headers = ["Fon Kodu", "Skor", "RSI", "MACD", "Fiyat (TL)", 
                  "Yatırımcı", "Hacim", "Kriterler"]
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws_trend.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
            cell.border = thin_border
        
        for row_idx, candidate in enumerate(trend_candidates, 2):
            data = [
                candidate['Fon'],
                candidate['Skor'],
                candidate['RSI'],
                candidate['MACD'],
                candidate['Fiyat'],
                candidate['Yatırımcı'],
                candidate['Hacim'],
                candidate['Kriterler']
            ]
            
            for col_idx, value in enumerate(data, 1):
                cell = ws_trend.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                if col_idx == 8:  # Kriterler
                    cell.alignment = wrap_alignment
                elif col_idx in [2, 3, 4, 5]:  # Skor, RSI, MACD, Fiyat
                    cell.alignment = center_alignment
        
        # Sütun genişlikleri
        column_widths = [12, 8, 8, 12, 12, 12, 15, 40]
        for idx, width in enumerate(column_widths, 1):
            ws_trend.column_dimensions[chr(64 + idx)].width = width
    
    # 5. PERFORMANS ANALİZİ SHEET
    ws_performance = wb.create_sheet(title="📊 Performans")
    
    # Başlık
    ws_performance['A1'] = "Momentum & Performans Analizi"
    ws_performance['A1'].font = subheader_font
    
    row = 3
    
    # Case 1: 3 Gün Art Arda
    ws_performance[f'A{row}'] = "① 3 Gün Art Arda ≥ %1.0"
    ws_performance[f'A{row}'].font = subheader_font
    row += 1
    
    if case1_rows:
        for fund in case1_rows:
            ws_performance[f'B{row}'] = fund['Fon']
            row += 1
    else:
        ws_performance[f'B{row}'] = "Kriterleri karşılayan fon yok"
        row += 1
    
    row += 1
    
    # Case 2: Son 3 Gün Toplam
    ws_performance[f'A{row}'] = "② Son 3 Gün Toplam ≥ %4.0"
    ws_performance[f'A{row}'].font = subheader_font
    row += 1
    
    if case2_rows:
        for fund in case2_rows:
            ws_performance[f'B{row}'] = fund['Fon']
            row += 1
    else:
        ws_performance[f'B{row}'] = "Kriterleri karşılayan fon yok"
        row += 1
    
    row += 1
    
    # Case 3: Haftalık
    ws_performance[f'A{row}'] = "③ Haftalık (5gün) Toplam ≥ %5.0"
    ws_performance[f'A{row}'].font = subheader_font
    row += 1
    
    if case3_rows:
        for fund in case3_rows:
            ws_performance[f'B{row}'] = fund['Fon']
            row += 1
    else:
        ws_performance[f'B{row}'] = "Kriterleri karşılayan fon yok"
        row += 1
    
    # Sütun genişlikleri
    ws_performance.column_dimensions['A'].width = 30
    ws_performance.column_dimensions['B'].width = 15
    
    # 6. UYARILAR SHEET
    if declining_rows:
        ws_alerts = wb.create_sheet(title="⚠️ Uyarılar")
        
        headers = ["Fon Kodu", "Uyarı Türü", "Kriterler"]
        
        for col_idx, header in enumerate(headers, 1):
            cell = ws_alerts.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = PatternFill("solid", fgColor="DC3545")
            cell.alignment = center_alignment
            cell.border = thin_border
        
        for row_idx, fund in enumerate(declining_rows, 2):
            data = [
                fund.get('Fon', fund.get('code', 'Bilinmiyor')),
                "Düşüş Sinyali",
                fund.get('Kriterler', fund.get('criteria', 'Detay yok'))
            ]
            
            for col_idx, value in enumerate(data, 1):
                cell = ws_alerts.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                cell.fill = red_fill
                if col_idx == 3:  # Kriterler
                    cell.alignment = wrap_alignment
        
        # Sütun genişlikleri
        ws_alerts.column_dimensions['A'].width = 12
        ws_alerts.column_dimensions['B'].width = 15
        ws_alerts.column_dimensions['C'].width = 40
    
    # Excel dosyasını kaydet
    filename = f"tefas_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    wb.save(filename)
    
    print(f"📊 Excel Rapor kaydedildi: {filename}")
    print(f"📂 Excel dosyasını açmak için: open {filename}")
    
    return filename

# ========= FONKSİYONLAR =========
def pct_series(df: pd.DataFrame) -> pd.DataFrame:
    if "date" not in df.columns:
        for c in df.columns:
            if "tarih" in c.lower():
                df = df.rename(columns={c: "date"})
    if "price" not in df.columns:
        for c in df.columns:
            if any(k in c.lower() for k in ["fiyat", "price"]):
                df = df.rename(columns={c: "price"})
    
    # CRITICAL FIX: Date conversion ekle
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values("date", ascending=True).dropna(subset=["price"]).reset_index(drop=True)
    df["pct"] = df["price"].pct_change() * 100.0
    return df

def safe_cum_pct(pcts: pd.Series) -> float:
    pcts = pcts.dropna()
    return float((pcts/100 + 1).prod() - 1) * 100.0 if not pcts.empty else 0.0

def fetch_fund_data(code: str, start: str, end: str):
    """TEFAS Crawler ile fon verisini getirir"""
    for attempt in range(RETRY_LIMIT):
        try:
            # TEFAS Crawler kullanarak veri çek
            df = crawler.fetch(start, end, code)
            if df.empty:
                return pd.DataFrame()  # Sessiz geç
            
            # CRITICAL FIX: Tarihleri datetime'a çevir ve düzgün sırala
            df['date'] = pd.to_datetime(df['date'])
            
            # ESKİDEN YENİYE doğru sırala (DÜZELTME)
            df = df.sort_values("date", ascending=True).dropna(subset=["price"]).reset_index(drop=True)
            
            # Yüzde değişimi hesapla
            df["pct"] = df["price"].pct_change() * 100.0
            
            # Debug: Tarih sıralamasını kontrol et
            if len(df) > 1:
                logger.debug(f"{code}: İlk tarih={df.iloc[0]['date']}, Son tarih={df.iloc[-1]['date']}")
            
            return df
        except Exception as e:
            logger.warning(f"{code} veri çekme hatası (deneme {attempt + 1}/{RETRY_LIMIT}): {e}")
            if attempt < RETRY_LIMIT - 1:
                time.sleep(0.5)  # Kısa bekleme
    
    return pd.DataFrame()

def get_fund_stats(df: pd.DataFrame):
    """Fon istatistiklerini hesaplar (yatırımcı sayısı, hacim vs.)"""
    if df.empty or len(df) < 7:
        return {
            'investor_count': 'N/A',
            'investor_change_week': 'N/A', 
            'volume': 'N/A',
            'volume_change_week': 'N/A'
        }
    
    # Veri tarihe göre sıralı olmalı (eskiden yeniye)
    # Bu yüzden iloc[-1] = en yeni veri, iloc[-7] = 7 gün önceki veri
    latest = df.iloc[-1]  # En yeni veri
    week_ago = df.iloc[-7] if len(df) >= 7 else df.iloc[0]  # 7 gün önceki veri
    
    # Yatırımcı sayısı ve haftalık değişim
    current_investors = latest.get('number_of_investors', 0) or 0
    week_investors = week_ago.get('number_of_investors', 0) or 0
    investor_change = current_investors - week_investors
    investor_change_sign = '+' if investor_change > 0 else ''
    
    # Hacim ve haftalık değişim
    current_volume = latest.get('market_cap', 0) or 0
    week_volume = week_ago.get('market_cap', 0) or 0
    volume_change = current_volume - week_volume
    volume_change_pct = (volume_change / week_volume * 100) if week_volume > 0 else 0
    volume_change_sign = '+' if volume_change > 0 else ''
    
    def format_number(num):
        """Sayıları okunabilir formatta göster"""
        if num >= 1_000_000_000:
            return f"{num/1_000_000_000:.1f}B"
        elif num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return f"{num:.0f}"
    
    return {
        'investor_count': int(current_investors) if current_investors > 0 else 'N/A',
        'investor_change_week': f"{investor_change_sign}{int(investor_change)}" if investor_change != 0 else "0",
        'volume': format_number(current_volume) if current_volume > 0 else 'N/A',
        'volume_change_week': f"{volume_change_sign}{format_number(volume_change)} ({volume_change_sign}{volume_change_pct:.1f}%)" if volume_change != 0 else "0 (0.0%)"
    }

def list_codes():
    """TEFAS Crawler ile fon kodlarını listeler"""
    # Önce bugünü dene, sonra geriye doğru git (iş günleri için)
    for days_back in range(0, 10):
        try:
            test_date = (date.today() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            print(f"🗺 Tarih deneniyor: {test_date}")
            all_funds = crawler.fetch(test_date)
            
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

def calc_indicators(df: pd.DataFrame) -> pd.DataFrame:
    close = df["price"]
    ma = close.rolling(20).mean()
    std = close.rolling(20).std()
    df["bb_upper"] = ma + 2 * std
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    return df

# ========= ANA =========
def main():
    # Panel verilerini yükle
    panel_data = load_panel_data()
    PORTFOLIO_FUNDS = panel_data["portfolio_funds"]
    
    end   = date.today() - timedelta(days=END_OFFSET_DAYS)
    start = end - timedelta(days=HISTORY_DAYS)

    codes = list_codes()
    if not codes:
        sys.exit("🧱 TEFAS verisi alınamadı. Lütfen internet bağlantınızı kontrol edin.")
    
    # PORTFÖY FONLARİNİ ÖNCELİKLENDİR - Rate limiting'e karşı korunma
    portfolio_codes = [code for code in PORTFOLIO_FUNDS if code in codes]
    other_codes = [code for code in codes if code not in PORTFOLIO_FUNDS]
    
    # Portföy fonlarını başa al, diğerlerini sonra
    prioritized_codes = portfolio_codes + other_codes
    
    if MAX_CODES:
        prioritized_codes = prioritized_codes[:MAX_CODES]

    print(f"\n📊 TEFAS Fon Tarama | CRAWLER MOD")
    print(f"Aralık: {start} → {end} | İncelenen fon sayısı: {len(prioritized_codes)}")
    print(f"🎯 Portföy fonları öncelik sırasında: {len(portfolio_codes)} fon")
    print(f"📊 Diğer fonlar: {len(other_codes)} fon")
    print(f"📏 Likidite filtresi: Min. {MIN_INVESTORS} yatırımcı (portföy fonları hariç)\n")

    print("ℹ️  Puanlama Sistemi (Basit):")
    print("")
    print("   📈 YÜKSELİŞ PUANLARI:")
    print("   • MACD Pozitif Kesişim: +2 puan (En güçlü sinyal)")
    print("   • Bollinger Bandı Kırılım: +1 puan")
    print("   • RSI 55-60 (Erken): +0.5 puan")
    print("   • RSI 60+ (Güçlü): +1 puan")
    print("")
    print("   📉 DÜŞÜŞ PUANLARI:")
    print("   • MACD Negatif Kesişim: +2 puan (Güçlü düşüş)")
    print("   • Bollinger Altına Kırılım: +1 puan")
    print("   • RSI 40'ın Altına Düşüş: +1 puan")
    print("")
    print("   🎯 Skor 1.5+ = Dikkat Edilecek Adaylar | Skor 3+ = Güçlü Sinyaller")
    print(f"   📏 Likidite filtresi: Minimum {MIN_INVESTORS} yatırımcı (portföy hariç)\n")

    signal_rows, case1_rows, case2_rows, case3_rows = [], [], [], []
    declining_rows = []  # Düşme trendi adayları
    portfolio_analysis = []  # Tüm portföy fonları analizi
    processed = 0
    filtered_out = 0  # Yatırımcı filtresi ile atlan fon sayısı
    start_time = time.time()
    
    print(f"🚀 Tarama başlatılıyor... Toplam {len(prioritized_codes)} fon analiz edilecek\n")
    
    for i, code in enumerate(prioritized_codes, 1):
        # Progress göstergesi - her 50 fonda bir güncelle
        if i % 50 == 0 or i == len(prioritized_codes):
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(prioritized_codes) - i) / rate if rate > 0 else 0
            
            # Portföy durumunu da göster
            portfolio_status = "🎯" if code in portfolio_codes else "📊"
            print(f"{portfolio_status} {i}/{len(prioritized_codes)} ({i/len(prioritized_codes)*100:.1f}%) | Hız: {rate:.1f} fon/sn | Kalan: {eta/60:.1f}dk")
        
        df = fetch_fund_data(code, start.isoformat(), end.isoformat())
        if df.empty or len(df) < 25:
            continue
        
        # Yatırımcı sayısı filtresi - minimum 50 yatırımcı olmalı
        latest_data = df.iloc[-1]
        current_investors = latest_data.get('number_of_investors', 0) or 0
        
        # Portföy fonlarını her zaman analiz et (yatırımcı sayısı düşük olsa bile)
        if code not in PORTFOLIO_FUNDS and current_investors < MIN_INVESTORS:
            filtered_out += 1
            # Debug bilgisi - sadece test amaçlı (ilk birkaç tane göster)
            if filtered_out <= 3:
                print(f"⚠️ {code}: {current_investors} yatırımcı (< {MIN_INVESTORS}) - atlandı")
            continue
        
        processed += 1
        df = calc_indicators(df)
        last, prev = df.iloc[-1], df.iloc[-2]
        bb_signal   = last["price"] > last["bb_upper"]
        macd_cross  = last["macd"] > last["macd_signal"] and prev["macd"] <= prev["macd_signal"]
        
        # RSI sinyalleri: Erken momentum için 55-60, Trend için 60+
        rsi_early_momentum = 55 <= last["rsi"] < 60 and prev["rsi"] < 55  # Erken momentum
        rsi_strong_trend = last["rsi"] >= 60 and prev["rsi"] < 60        # Güçlü trend
        
        # Skor hesaplama
        score = (2 if macd_cross else 0) + (1 if bb_signal else 0) + (0.5 if rsi_early_momentum else 0) + (1 if rsi_strong_trend else 0)
        
        # Düşme trendi sinyalleri
        bb_break_down = last["price"] < last["bb_upper"] * 0.98  # Bollinger altına düşüm
        macd_cross_down = last["macd"] < last["macd_signal"] and prev["macd"] >= prev["macd_signal"]
        rsi_fall = last["rsi"] <= 40 and prev["rsi"] > 40
        decline_score = (2 if macd_cross_down else 0) + (1 if bb_break_down else 0) + (1 if rsi_fall else 0)
        
        # Sadece skor 1.5 ve üzeri adayları kaydet
        if score >= 1.5:
            # Puan kaynaklarını belirle
            criteria = []
            if macd_cross:
                criteria.append("MACD Kesişim (+2)")
            if bb_signal:
                criteria.append("Bollinger Kırılım (+1)")
            if rsi_early_momentum:
                criteria.append("RSI Erken Momentum 55-60 (+0.5)")
            if rsi_strong_trend:
                criteria.append("RSI Güçlü Trend 60+ (+1)")
            
            # Fon istatistiklerini hesapla
            fund_stats = get_fund_stats(df)
            
            signal_rows.append({
                "Fon": code,
                "Skor": score,
                "Kriterler": ", ".join(criteria),
                "RSI": round(last["rsi"], 1),
                "MACD": round(last["macd"], 4),
                "Signal": round(last["macd_signal"], 4),
                "Fiyat": round(last["price"], 4),
                "Yatırımcı": fund_stats['investor_count'],
                "Yatırımcı_Değişim": fund_stats['investor_change_week'],
                "Hacim": fund_stats['volume'],
                "Hacim_Değişim": fund_stats['volume_change_week']
            })
        
        # Portföydeki tüm fonların analizini kaydet
        if code in PORTFOLIO_FUNDS:
            # Her fon için ayrı fund_stats hesapla
            fund_stats = get_fund_stats(df)
            
            # Yükseliş kriterleri
            upward_criteria = []
            if macd_cross:
                upward_criteria.append("MACD Pozitif Kesişim (+2)")
            if bb_signal:
                upward_criteria.append("Bollinger Kırılım (+1)")
            if rsi_early_momentum:
                upward_criteria.append("RSI Erken Momentum 55-60 (+0.5)")
            if rsi_strong_trend:
                upward_criteria.append("RSI Güçlü Trend 60+ (+1)")
            
            # Düşüş kriterleri
            decline_criteria = []
            if macd_cross_down:
                decline_criteria.append("MACD Düşüm (+2)")
            if bb_break_down:
                decline_criteria.append("Bollinger Düşüm (+1)")
            if rsi_fall:
                decline_criteria.append("RSI Düşüm (+1)")
            
            # Durum analizi
            if score >= 1.5:
                trend_status = "🔥 Güçlü Yükseliş" if score >= 3 else "📈 Yükseliş Sinyali"
                criteria_text = ", ".join(upward_criteria) if upward_criteria else "Yükseliş sinyalleri"
            elif decline_score >= 1.5:
                trend_status = "🔴 Güçlü Düşüş" if decline_score >= 3 else "📉 Düşüş Sinyali"
                criteria_text = ", ".join(decline_criteria) if decline_criteria else "Düşüş sinyalleri"
            else:
                trend_status = "➡️ Durağan/Kararsız"
                criteria_text = "Belirgin trend sinyali yok"
            
            portfolio_analysis.append({
                "Fon": code,
                "Trend_Status": trend_status,
                "Yükseliş_Skor": score,
                "Düşüş_Skor": decline_score,
                "Kriterler": criteria_text,
                "RSI": round(last["rsi"], 1),
                "MACD": round(last["macd"], 4),
                "Signal": round(last["macd_signal"], 4),
                "Fiyat": round(last["price"], 4),
                "Yatırımcı": fund_stats['investor_count'],
                "Yatırımcı_Değişim": fund_stats['investor_change_week'],
                "Hacim": fund_stats['volume'],
                "Hacim_Değişim": fund_stats['volume_change_week']
            })
        
        # Portföydeki fonlar için düşme trendi analizi (skor 1.5 ve üzeri)
        if code in PORTFOLIO_FUNDS and decline_score >= 1.5:
            decline_criteria = []
            if macd_cross_down:
                decline_criteria.append("MACD Düşüm (+2)")
            if bb_break_down:
                decline_criteria.append("Bollinger Kırılım (+1)")
            if rsi_fall:
                decline_criteria.append("RSI Düşüm (+1)")
            
            # Fon istatistiklerini hesapla (eğer daha önce hesaplanmadıysa)
            if 'fund_stats' not in locals() or fund_stats is None:
                fund_stats = get_fund_stats(df)
            
            declining_rows.append({
                "Fon": code,
                "Skor": decline_score,
                "Kriterler": ", ".join(decline_criteria),
                "RSI": round(last["rsi"], 1),
                "MACD": round(last["macd"], 4),
                "Signal": round(last["macd_signal"], 4),
                "Fiyat": round(last["price"], 4),
                "Yatırımcı": fund_stats['investor_count'],
                "Yatırımcı_Değişim": fund_stats['investor_change_week'],
                "Hacim": fund_stats['volume'],
                "Hacim_Değişim": fund_stats['volume_change_week']
            })

        def fmt(lst): return [round(x, 2) if pd.notna(x) else None for x in lst]
        def dts(lst): return [str(x)[:10] for x in lst]
        last3 = df.tail(CASE1_STREAK_DAYS)
        if (last3["pct"].dropna() >= CASE1_MIN_DAILY).all():
            case1_rows.append({"Fon": code, "Tarihler": dts(last3["date"]),
                               "Günlük %": fmt(last3["pct"]),
                               "Kümülatif % (3gün)": round(safe_cum_pct(last3["pct"]), 2)})
        last3b = df.tail(CASE2_WINDOW_DAYS)
        total3 = safe_cum_pct(last3b["pct"])
        if total3 >= CASE2_MIN_CUM:
            case2_rows.append({"Fon": code, "Tarihler": dts(last3b["date"]),
                               "Günlük %": fmt(last3b["pct"]),
                               "Kümülatif % (3gün)": round(total3, 2)})
        last5 = df.tail(CASE3_WINDOW_DAYS)
        total5 = safe_cum_pct(last5["pct"])
        if total5 >= CASE3_MIN_CUM:
            case3_rows.append({"Fon": code, "Tarihler": dts(last5["date"]),
                               "Günlük %": fmt(last5["pct"]),
                               "Kümülatif % (5gün)": round(total5, 2)})

        time.sleep(SLEEP_BETWEEN)

    # Skor 1.5-2.5 olanlar (Erken Momentum) ve 3+ olanlar (Trend) ayrı ayrı göster
    # User rule: For early trend candidates, update RSI value to 55-60 and set score to 2, renaming them as early momentum candidates
    early_momentum = []
    trend_candidates = []
    
    for r in signal_rows:
        if 1.5 <= r["Skor"] < 3:
            # Early momentum candidate - update RSI value to 55-60 range and set score to 2
            updated_candidate = r.copy()
            updated_candidate["RSI"] = min(60, max(55, updated_candidate["RSI"]))
            updated_candidate["Skor"] = 2
            early_momentum.append(updated_candidate)
        elif r["Skor"] >= 3:
            # For those with score 3 and above, keep the current RSI value and name them as trend candidates
            trend_candidates.append(r)
    
    # Adayları JSON'a kaydet
    update_candidates(panel_data, early_momentum, trend_candidates)
    
    print("\n=============================================")
    print("🚀  ERKEN MOMENTUM ADAYLARI  🚀")
    if early_momentum:
        print(f"\n🟡 {len(early_momentum)} adet erken momentum adayı bulundu (Skor: 1.5-2.5)\n")
        for r in sorted(early_momentum, key=lambda x: x["RSI"], reverse=True):
            print(f"Fon: {r['Fon']} | 🔡 Erken Momentum (Skor: {r['Skor']})")
            print(f"📊 Kriterler   : {r['Kriterler']}")
            print(f"📈 RSI         : {r['RSI']}")
            print(f"📉 MACD        : {r['MACD']} | Signal: {r['Signal']}")
            print(f"💰 Fiyat       : {r['Fiyat']}")
            investor_str = f"{r['Yatırımcı']:,}" if isinstance(r['Yatırımcı'], int) else str(r['Yatırımcı'])
            print(f"👥 Yatırımcı    : {investor_str} kişi (1 hafta: {r['Yatırımcı_Değişim']})")
            print(f"📊 Hacim       : {r['Hacim']} TL (1 hafta: {r['Hacim_Değişim']})")
            print("─" * 60)
    else:
        print("\n🔍 Erken momentum kriterleri karşılayan fon bulunamadı (Skor: 1.5-2.5)")
    
    print("\n\n=============================================")
    print("💎  TREND ADAYLARI  💎")
    if trend_candidates:
        print(f"\n💎 {len(trend_candidates)} adet trend adayı bulundu (Skor ≥3)\n")
        for r in sorted(trend_candidates, key=lambda x: x["Skor"], reverse=True):
            trend_strength = "💎 Güçlü Trend"
            print(f"Fon: {r['Fon']} | {trend_strength} (Skor: {r['Skor']})")
            print(f"📊 Kriterler   : {r['Kriterler']}")
            print(f"📈 RSI         : {r['RSI']}")
            print(f"📉 MACD        : {r['MACD']} | Signal: {r['Signal']}")
            print(f"💰 Fiyat       : {r['Fiyat']}")
            investor_str = f"{r['Yatırımcı']:,}" if isinstance(r['Yatırımcı'], int) else str(r['Yatırımcı'])
            print(f"👥 Yatırımcı    : {investor_str} kişi (1 hafta: {r['Yatırımcı_Değişim']})")
            print(f"📊 Hacim       : {r['Hacim']} TL (1 hafta: {r['Hacim_Değişim']})")
            print("─" * 60)
    else:
        print("\n🔍 Güçlü trend kriterleri karşılayan fon bulunamadı (Skor ≥3)")
    
    # Portföy Analizi - Tüm portföy fonları
    print("\n\n=============================================")
    print("💼  PORTFÖY ANALİZİ  💼")
    print(f"📋 Takip edilen portföy fonları: {', '.join(PORTFOLIO_FUNDS)}")
    
    # Portföy fonları için eksik analizleri tamamla
    analyzed_portfolio_codes = {fund['Fon'] for fund in portfolio_analysis}
    missing_portfolio_funds = [code for code in PORTFOLIO_FUNDS if code not in analyzed_portfolio_codes]
    
    if missing_portfolio_funds:
        print(f"\n🔎 Eksik portföy fonları analiz ediliyor: {', '.join(missing_portfolio_funds)}\n")
        
        for fund_code in missing_portfolio_funds:
            print(f"📊 {fund_code} analiz ediliyor...")
            df = fetch_fund_data(fund_code, start.isoformat(), end.isoformat())
            
            if df.empty or len(df) < 25:
                print(f"⚠️ {fund_code}: Yeterli veri bulunamadı")
                # Veri bulunamasa bile placeholder ekle
                portfolio_analysis.append({
                    "Fon": fund_code,
                    "Trend_Status": "❌ Veri Bulunamadı",
                    "Yükseliş_Skor": 0,
                    "Düşüş_Skor": 0,
                    "Kriterler": "Veri yetersiz",
                    "RSI": "N/A",
                    "MACD": "N/A",
                    "Signal": "N/A",
                    "Fiyat": "N/A",
                    "Yatırımcı": "N/A",
                    "Yatırımcı_Değişim": "N/A",
                    "Hacim": "N/A",
                    "Hacim_Değişim": "N/A"
                })
                print("─" * 60)
                continue
            
            # Teknik analiz
            df = calc_indicators(df)
            last, prev = df.iloc[-1], df.iloc[-2]
            
            # Sinyaller
            bb_signal = last["price"] > last["bb_upper"]
            macd_cross = last["macd"] > last["macd_signal"] and prev["macd"] <= prev["macd_signal"]
            rsi_early_momentum = 55 <= last["rsi"] < 60 and prev["rsi"] < 55
            rsi_strong_trend = last["rsi"] >= 60 and prev["rsi"] < 60
            
            # Düşüş sinyalleri
            bb_break_down = last["price"] < last["bb_upper"] * 0.98
            macd_cross_down = last["macd"] < last["macd_signal"] and prev["macd"] >= prev["macd_signal"]
            rsi_fall = last["rsi"] <= 40 and prev["rsi"] > 40
            
            # Skorlar
            score = (2 if macd_cross else 0) + (1 if bb_signal else 0) + (0.5 if rsi_early_momentum else 0) + (1 if rsi_strong_trend else 0)
            decline_score = (2 if macd_cross_down else 0) + (1 if bb_break_down else 0) + (1 if rsi_fall else 0)
            
            # Kriterler
            upward_criteria = []
            if macd_cross: upward_criteria.append("MACD Pozitif Kesişim (+2)")
            if bb_signal: upward_criteria.append("Bollinger Kırılım (+1)")
            if rsi_early_momentum: upward_criteria.append("RSI Erken Momentum 55-60 (+0.5)")
            if rsi_strong_trend: upward_criteria.append("RSI Güçlü Trend 60+ (+1)")
            
            decline_criteria = []
            if macd_cross_down: decline_criteria.append("MACD Düşüm (+2)")
            if bb_break_down: decline_criteria.append("Bollinger Düşüm (+1)")
            if rsi_fall: decline_criteria.append("RSI Düşüm (+1)")
            
            # Durum analizi
            if score >= 1.5:
                trend_status = "🔥 Güçlü Yükseliş" if score >= 3 else "📈 Yükseliş Sinyali"
                criteria_text = ", ".join(upward_criteria) if upward_criteria else "Yükseliş sinyalleri"
            elif decline_score >= 1.5:
                trend_status = "🔴 Güçlü Düşüş" if decline_score >= 3 else "📉 Düşüş Sinyali"
                criteria_text = ", ".join(decline_criteria) if decline_criteria else "Düşüş sinyalleri"
            else:
                trend_status = "➡️ Durağan/Kararsız"
                criteria_text = "Belirgin trend sinyali yok"
            
            # Fon istatistikleri
            fund_stats = get_fund_stats(df)
            
            # Portföy analizine ekle
            portfolio_analysis.append({
                "Fon": fund_code,
                "Trend_Status": trend_status,
                "Yükseliş_Skor": score,
                "Düşüş_Skor": decline_score,
                "Kriterler": criteria_text,
                "RSI": round(last["rsi"], 1),
                "MACD": round(last["macd"], 4),
                "Signal": round(last["macd_signal"], 4),
                "Fiyat": round(last["price"], 4),
                "Yatırımcı": fund_stats['investor_count'],
                "Yatırımcı_Değişim": fund_stats['investor_change_week'],
                "Hacim": fund_stats['volume'],
                "Hacim_Değişim": fund_stats['volume_change_week']
            })
            
            # Sonuçları göster
            print(f"Fon: {fund_code} | {trend_status}")
            print(f"📊 Kriterler   : {criteria_text}")
            print(f"📈 RSI         : {round(last['rsi'], 1)}")
            print(f"📉 MACD        : {round(last['macd'], 4)} | Signal: {round(last['macd_signal'], 4)}")
            print(f"💰 Fiyat       : {round(last['price'], 4)}")
            investor_str = f"{fund_stats['investor_count']:,}" if isinstance(fund_stats['investor_count'], int) else str(fund_stats['investor_count'])
            print(f"👥 Yatırımcı    : {investor_str} kişi (1 hafta: {fund_stats['investor_change_week']})")
            print(f"📊 Hacim       : {fund_stats['volume']} TL (1 hafta: {fund_stats['volume_change_week']})")
            print("─" * 60)
            
            # Düşüş uyarısı
            if decline_score >= 1.5:
                declining_rows.append({
                    "Fon": fund_code,
                    "Skor": decline_score,
                    "Kriterler": ", ".join(decline_criteria)
                })
    
    else:
        print(f"\n📊 Portföyünüzdeki {len(portfolio_analysis)} fonun detaylı analizi:\n")
        for r in portfolio_analysis:
            print(f"Fon: {r['Fon']} | {r['Trend_Status']}")
            print(f"📊 Kriterler   : {r['Kriterler']}")
            print(f"📈 RSI         : {r['RSI']}")
            print(f"📉 MACD        : {r['MACD']} | Signal: {r['Signal']}")
            print(f"💰 Fiyat       : {r['Fiyat']}")
            investor_str = f"{r['Yatırımcı']:,}" if isinstance(r['Yatırımcı'], int) else str(r['Yatırımcı'])
            print(f"👥 Yatırımcı    : {investor_str} kişi (1 hafta: {r['Yatırımcı_Değişim']})")
            print(f"📊 Hacim       : {r['Hacim']} TL (1 hafta: {r['Hacim_Değişim']})")
            print("─" * 60)
    
    # Düşme uyarısı (eğer varsa)
    if declining_rows:
        print("\n\n⚠️  PORTFÖY UYARISI - DÜŞME SİNYALİ  ⚠️")
        print(f"🚨 Portföyünüzde {len(declining_rows)} fonda düşme sinyali tespit edildi!")
        for r in declining_rows:
            print(f"🔴 {r['Fon']}: Düşüş skoru {r['Skor']} - {r['Kriterler']}")

    def print_case(rows, title, key):
        print("\n" + "="*40)
        print(title)
        if not rows:
            print("\n— bulunamadı —")
            return
        for r in rows:
            print(f"\nFon: {r['Fon']}")
            print(f"Tarihler : {r['Tarihler']}")
            print(f"Günlük % : {r['Günlük %']}")
            print(f"Kümülatif: %{r[key]}")
            print("---------------------------------------------")

    print_case(case1_rows, f"① 3 gün art arda ≥ %{CASE1_MIN_DAILY}", "Kümülatif % (3gün)")
    print_case(case2_rows, f"② Son 3 gün toplam ≥ %{CASE2_MIN_CUM}", "Kümülatif % (3gün)")
    print_case(case3_rows, f"③ Haftalık (5gün) toplam ≥ %{CASE3_MIN_CUM}", "Kümülatif % (5gün)")
    
    # Final özet raporu
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"📊 TARAMA TAMAMLANDI | Süre: {total_time/60:.1f} dakika")
    print(f"{'='*60}")
    print(f"📈 Toplam incelenen fon       : {len(codes):,}")
    print(f"✅ Başarıyla analiz edilen    : {processed:,}")
    print(f"📏 Likidite filtresi (<{MIN_INVESTORS} yatırımcı): {filtered_out:,} fon atlandı")
    print(f"🚀 Erken momentum adayı       : {len(early_momentum)}")
    print(f"💎 Trend adayı               : {len(trend_candidates)}")
    print(f"📉 Düşüş trend adayı          : {len(declining_rows)}")
    print(f"🔥 Momentum adayı (Kasa 2)     : {len(case2_rows)}")
    print(f"📅 Haftalık performans (Kasa 3): {len(case3_rows)}")
    print(f"⚡ Ortalama hız               : {processed/total_time:.1f} fon/saniye (analiz edilen)")
    
    # TEFAS Günlük Takip Paneli
    print_daily_tracking_panel_with_cases(panel_data, portfolio_analysis, early_momentum, trend_candidates, declining_rows, case1_rows, case2_rows, case3_rows)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 İptal edildi.")
        sys.exit(1)
