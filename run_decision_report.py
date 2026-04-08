#!/usr/bin/env python3
"""
Karar Raporu Oluşturucu
Mevcut TEFAS verilerini kullanarak karar raporu üretir
"""

import json
import os
from datetime import datetime, timedelta
from data_provider import FundDataProvider
from technical_analyzer import TechnicalAnalyzer
from panel_manager import PanelManager
from decision_engine import DecisionEngine, process_json_input
from email_reporter import EmailReporter
from config import config
import score_history_manager as shm

# Output dizini
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_fund_statistics(fund_data, fund_code):
    """Fon istatistiklerini hesapla"""
    if fund_data is None or len(fund_data) < 7:
        return {}
    
    stats = {}
    
    try:
        # Son değerler
        current = fund_data.iloc[-1]
        week_ago = fund_data.iloc[-7] if len(fund_data) >= 7 else fund_data.iloc[0]
        
        # Yatırımcı değişimi (7 gün)
        current_inv = current.get('number_of_investors', 0) or 0
        week_inv = week_ago.get('number_of_investors', 0) or 0
        if week_inv > 0:
            stats['investor_change_7d'] = ((current_inv - week_inv) / week_inv) * 100
        
        # Hacim değişimi (7 gün)
        current_vol = current.get('market_cap', 0) or 0
        week_vol = week_ago.get('market_cap', 0) or 0
        if week_vol > 0:
            stats['volume_change_7d'] = ((current_vol - week_vol) / week_vol) * 100
        
        # Volatilite (son 20 gün)
        if len(fund_data) >= 20:
            recent_returns = fund_data.tail(20)['pct'].dropna()
            if len(recent_returns) >= 10:
                stats['volatility'] = recent_returns.std()
                avg_return = recent_returns.mean()
                if stats['volatility'] > 0:
                    stats['sharpe'] = avg_return / stats['volatility']
        
        # Periyodik getiriler
        if len(fund_data) >= 1:
            stats['pct_1d'] = fund_data.iloc[-1].get('pct', 0) or 0
        if len(fund_data) >= 3:
            stats['pct_3d'] = fund_data.tail(3)['pct'].sum()
        if len(fund_data) >= 5:
            stats['pct_1w'] = fund_data.tail(5)['pct'].sum()
            stats['pct_5d'] = fund_data.tail(5)['pct'].sum()  # ret_5d için
            stats['positive_days_5'] = (fund_data.tail(5)['pct'] > 0).sum()
        
    except Exception as e:
        print(f"   ⚠️ {fund_code} istatistik hatası: {e}")
    
    return stats


def calculate_trend_avcisi(funds_data: list, decision_engine) -> list:
    """
    TREND_AVCISI: Erken trend radarları
    
    Koşullar:
    - score_final >= 50
    - macd_bull == True
    - RSI 50-65
    - ret_5d < 7%
    - delta_score_3g >= +4
    
    Sıralama: score_final DESC, delta_score DESC
    """
    # Delta score'ları al (3 günlük)
    deltas = shm.get_all_deltas(days=3)
    
    if not deltas:
        return []  # Yeterli geçmiş veri yok
    
    candidates = []
    
    for fd in funds_data:
        code = fd["fund_code"]
        score = fd.get("score", 0)
        rsi = fd.get("rsi", 0)
        macd = fd.get("macd", 0)
        macd_signal = fd.get("macd_signal", 0)
        ret_5d = fd.get("ret_5d", 0) or 0
        
        # score_final hesapla
        score_final = decision_engine._calculate_score_final(score, rsi, ret_5d)
        
        # MACD bull
        macd_bull = macd > macd_signal if macd and macd_signal else False
        
        # Delta score
        delta = deltas.get(code, 0)
        
        # TREND_AVCISI koşulları
        if (score_final >= 50 and
            macd_bull and
            50 <= rsi <= 65 and
            ret_5d < 7 and
            delta >= 4):
            
            candidates.append({
                "code": code,
                "score_final": score_final,
                "delta": delta,
                "rsi": rsi,
                "ret_5d": ret_5d,
                "macd_bull": macd_bull
            })
    
    # Sırala: score_final DESC, delta DESC
    candidates.sort(key=lambda x: (-x["score_final"], -x["delta"]))
    
    return candidates


def run_decision_report(scan_all=False, min_score=50):
    """Ana rapor oluşturma fonksiyonu
    
    Args:
        scan_all: True ise tüm fonları tara, False ise sadece panel fonlarını
        min_score: Minimum skor filtresi (varsayılan 50)
    """
    print("\n" + "="*50)
    print("🔥 KARAR RAPORU OLUŞTURUCU")
    print("="*50)
    
    # Modülleri başlat
    data_provider = FundDataProvider()
    technical_analyzer = TechnicalAnalyzer()
    panel_manager = PanelManager()
    decision_engine = DecisionEngine()
    
    if scan_all:
        # Tüm fonları tara
        print("\n🔍 Tüm fonlar taranıyor...")
        target_funds = data_provider.get_fund_codes()
        print(f"   ✅ {len(target_funds)} fon kodu yüklendi")
    else:
        # Panel verilerini al
        panel_data = panel_manager.get_panel_data()
        portfolio_funds = panel_data.get('portfolio_funds', [])
        watch_funds = panel_data.get('watch_funds', [])
        
        # Analiz edilecek fonlar (portföy + izleme listesi)
        target_funds = list(set(portfolio_funds + watch_funds))
        
        if not target_funds:
            # Eğer panel boşsa, örnek fonlar kullan
            target_funds = ['TLY', 'DFI', 'PHE', 'GAF', 'RDF', 'DAH', 'TZD', 'MAC', 'AK4', 'YAY']
    
    print(f"\n📊 {len(target_funds)} fon analiz ediliyor...")
    
    # Tarih aralığı
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now() - timedelta(days=45)).date().isoformat()
    
    # Her fon için veri topla
    funds_data = []
    
    for fund_code in target_funds:
        try:
            # Fon verisi al
            fund_data = data_provider.get_fund_data(fund_code, start_date, end_date)
            
            if fund_data is None or len(fund_data) < 20:
                print(f"   ⚠️ {fund_code}: Yetersiz veri")
                continue
            
            # Teknik analiz
            analysis = technical_analyzer.analyze_fund(fund_data, fund_code)
            
            # İstatistikler
            stats = get_fund_statistics(fund_data, fund_code)
            
            # Dünkü MACD (2 gün confirm için)
            macd_yesterday = None
            macd_signal_yesterday = None
            if hasattr(analysis, 'macd_yesterday'):
                macd_yesterday = analysis.macd_yesterday
                macd_signal_yesterday = analysis.macd_signal_yesterday
            
            # ret_5d (5 günlük getiri)
            ret_5d = stats.get('pct_5d', 0) or 0
            
            # Decision engine formatına dönüştür
            fund_entry = {
                "fund_code": fund_code,
                "score": int(analysis.score),
                "rsi": analysis.rsi,
                "macd": analysis.macd,
                "macd_signal": analysis.macd_signal,
                "macd_yesterday": macd_yesterday,
                "macd_signal_yesterday": macd_signal_yesterday,
                "ret_5d": ret_5d,
                "price": analysis.price,
                "fund_statistics": stats
            }
            
            funds_data.append(fund_entry)
            print(f"   ✅ {fund_code}: Skor={analysis.score}, RSI={analysis.rsi:.1f}")
            
        except Exception as e:
            print(f"   ❌ {fund_code}: Hata - {e}")
    
    if not funds_data:
        print("\n❌ Analiz edilecek fon bulunamadı!")
        return
    
    # Portföy fonlarını al
    panel_data = panel_manager.get_panel_data()
    portfolio_funds = panel_data.get('portfolio_funds', [])
    
    # Karar raporu oluştur
    print("\n" + "="*50)
    results = decision_engine.analyze_batch(funds_data, portfolio_funds=portfolio_funds)
    
    # Liste formatında yazdır
    print("🔥 KARAR RAPORU")
    print("="*50)
    print(decision_engine.generate_report(results, mode="list"))
    print("="*50)
    
    # Özet
    print("\n📊 ÖZET:")
    sat_count = sum(1 for r in results.values() if r.decision.value == "SAT")
    azalt_count = sum(1 for r in results.values() if r.decision.value == "AZALT")
    al_count = sum(1 for r in results.values() if r.decision.value == "AL")
    tut_count = sum(1 for r in results.values() if r.decision.value == "TUT")
    bekle_count = sum(1 for r in results.values() if r.decision.value == "BEKLE")
    alma_count = sum(1 for r in results.values() if r.decision.value == "ALMA")
    
    print(f"   🔴 SAT: {sat_count}")
    print(f"   ⚠️ AZALT: {azalt_count}")
    print(f"   ✅ AL: {al_count}")
    print(f"   🟡 TUT: {tut_count}")
    print(f"   ⏳ BEKLE: {bekle_count}")
    print(f"   ❌ ALMA: {alma_count}")
    
    # HTML rapor oluştur
    html_content = decision_engine.generate_html_report(
        results, 
        portfolio_funds=portfolio_funds,
        title="TEFAS Karar Raporu"
    )
    
    html_file = "karar_raporu.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 HTML Karar Raporu: {html_file}")
    print(f"🔍 Açmak için: open {html_file}")
    
    # JSON çıktı
    json_output = decision_engine._generate_json_report(results)
    
    return json_output, html_file


def run_full_decision_report():
    """
    TÜM TEFAS FONLARINI TARA (1800+)
    Portföy fonları öncelikli analiz edilir
    """
    print("\n" + "="*60)
    print("🔥 TAM KARAR RAPORU - TÜM FONLAR")
    print("="*60)
    
    data_provider = FundDataProvider()
    technical_analyzer = TechnicalAnalyzer()
    panel_manager = PanelManager()
    decision_engine = DecisionEngine()
    
    # Panel verilerini al
    panel_data = panel_manager.get_panel_data()
    portfolio_funds = panel_data.get('portfolio_funds', [])
    
    # TÜM FONLARI AL
    print("\n🔍 Tüm TEFAS fonları yükleniyor...")
    all_funds = data_provider.get_fund_codes()
    print(f"   ✅ {len(all_funds)} fon kodu yüklendi")
    
    # Portföy fonlarını öne al
    target_funds = portfolio_funds + [f for f in all_funds if f not in portfolio_funds]
    
    print(f"\n💼 Portföy: {portfolio_funds}")
    print(f"📊 Toplam taranacak: {len(target_funds)} fon")
    
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now() - timedelta(days=45)).date().isoformat()
    
    funds_data = []
    
    for i, fund_code in enumerate(target_funds):
        try:
            fund_data = data_provider.get_fund_data(fund_code, start_date, end_date)
            if fund_data is None or len(fund_data) < 20:
                continue
            
            analysis = technical_analyzer.analyze_fund(fund_data, fund_code)
            stats = get_fund_statistics(fund_data, fund_code)
            
            # Dünkü MACD
            macd_yesterday = getattr(analysis, 'macd_yesterday', None)
            macd_signal_yesterday = getattr(analysis, 'macd_signal_yesterday', None)
            ret_5d = stats.get('pct_5d', 0) or 0
            
            funds_data.append({
                "fund_code": fund_code,
                "score": int(analysis.score),
                "rsi": analysis.rsi,
                "macd": analysis.macd,
                "macd_signal": analysis.macd_signal,
                "macd_yesterday": macd_yesterday,
                "macd_signal_yesterday": macd_signal_yesterday,
                "ret_5d": ret_5d,
                "price": analysis.price,
                "fund_statistics": stats
            })
            
            # Her 10 fonda bir ilerleme göster
            if (i + 1) % 10 == 0:
                print(f"   ⏳ {i+1}/{len(target_funds)} analiz edildi...")
                
        except Exception as e:
            pass
    
    print(f"\n✅ {len(funds_data)} fon analiz edildi")
    
    # --- TASK 1: Daily Features Snapshot Export ---
    today_str = datetime.now().strftime("%Y-%m-%d")
    features_file = os.path.join(OUTPUT_DIR, f"daily_features_{today_str}.json")
    
    # funds_data'ya is_in_portfolio ekle ve export için hazırla
    features_export = []
    for fd in funds_data:
        code = fd["fund_code"]
        macd = fd.get("macd", 0)
        macd_signal = fd.get("macd_signal", 0)
        macd_yesterday = fd.get("macd_yesterday", None)
        macd_signal_yesterday = fd.get("macd_signal_yesterday", None)
        
        # MACD sinyalleri
        macd_bull = macd > macd_signal if macd and macd_signal else False
        macd_bull_confirm = False
        macd_bear_confirm = False
        if macd_yesterday is not None and macd_signal_yesterday is not None:
            macd_bull_confirm = macd_bull and (macd_yesterday > macd_signal_yesterday)
            macd_bear_confirm = (macd < macd_signal) and (macd_yesterday < macd_signal_yesterday)
        
        features_export.append({
            "code": code,
            "is_in_portfolio": code in portfolio_funds,
            "rsi": round(float(fd.get("rsi", 0)), 2),
            "score": int(fd.get("score", 0)),
            "score_final": int(decision_engine._calculate_score_final(
                fd.get("score", 0), fd.get("rsi", 0), fd.get("ret_5d", 0)
            )),
            "macd": round(float(macd), 6) if macd else 0,
            "macd_signal": round(float(macd_signal), 6) if macd_signal else 0,
            "macd_bull": bool(macd_bull),
            "macd_bull_confirm": bool(macd_bull_confirm),
            "macd_bear_confirm": bool(macd_bear_confirm),
            "ret_5d": round(float(fd.get("ret_5d", 0)), 2)
        })
    
    with open(features_file, 'w', encoding='utf-8') as f:
        json.dump({
            "date": today_str,
            "portfolio": portfolio_funds,
            "count": len(features_export),
            "funds": features_export
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 Feature snapshot: {features_file}")
    
    # Karar raporu (portföy fonlarını geçir - SAT/AZALT kararları için)
    results = decision_engine.analyze_batch(funds_data, portfolio_funds=portfolio_funds)
    
    # Konsol çıktısı - WhatsApp modu (Top 5)
    print("\n" + "="*60)
    print("📱 KARAR RAPORU")
    print("="*60)
    print(decision_engine.generate_report(results, mode="whatsapp", portfolio_funds=portfolio_funds))
    print("="*60)
    
    # Özet
    sat_count = sum(1 for r in results.values() if r.decision.value == "SAT")
    azalt_count = sum(1 for r in results.values() if r.decision.value == "AZALT")
    al_count = sum(1 for r in results.values() if r.decision.value == "AL")
    alinabilir_count = sum(1 for r in results.values() if r.decision.value == "ALINABİLİR ADAY")
    tut_count = sum(1 for r in results.values() if r.decision.value == "TUT")
    bekle_count = sum(1 for r in results.values() if r.decision.value == "BEKLE")
    alma_count = sum(1 for r in results.values() if r.decision.value == "ALMA")
    
    # AL sayısı kontrolü (kota uygulaması sonrası)
    al_early = sum(1 for r in results.values() if r.decision.value == "AL" and r.al_type == "EARLY")
    al_breakout = sum(1 for r in results.values() if r.decision.value == "AL" and r.al_type == "BREAKOUT")
    
    print(f"\n📊 ÖZET: SAT={sat_count} | AZALT={azalt_count} | AL={al_count} | ADAY={alinabilir_count} | TUT={tut_count} | BEKLE={bekle_count} | ALMA={alma_count}")
    print(f"⚙️  Trend Threshold: {decision_engine.SCORE_TREND}")
    
    # HTML rapor
    html_content = decision_engine.generate_html_report(
        results,
        portfolio_funds=portfolio_funds,
        title="TEFAS Karar Raporu"
    )
    
    html_file = "karar_raporu.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 HTML Rapor: {html_file}")
    
    # --- TASK 2: Decision Report JSON Export ---
    decision_file = os.path.join(OUTPUT_DIR, f"decision_report_{today_str}.json")
    
    decision_export = []
    for code, res in results.items():
        decision_export.append({
            "code": code,
            "decision": res.decision.value,
            "reason": res.reason,
            "rsi": round(res.rsi, 2),
            "score": res.score,
            "score_final": res.score_final,
            "al_type": res.al_type or None,
            "bekle_type": res.bekle_type.value if res.bekle_type else None
        })
    
    with open(decision_file, 'w', encoding='utf-8') as f:
        json.dump({
            "date": today_str,
            "portfolio": portfolio_funds,
            "threshold": {
                "SCORE_TREND": decision_engine.SCORE_TREND,
                "SCORE_STRONG_TREND": decision_engine.SCORE_STRONG_TREND,
                "SCORE_BREAKOUT": decision_engine.SCORE_BREAKOUT
            },
            "summary": {
                "SAT": sat_count,
                "AZALT": azalt_count,
                "AL": al_count,
                "ALINABILIR": alinabilir_count,
                "TUT": tut_count,
                "BEKLE": bekle_count,
                "ALMA": alma_count
            },
            "decisions": decision_export
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Decision report: {decision_file}")
    
    # --- Score History Kaydet ---
    daily_scores = {fd["fund_code"]: int(fd["score"]) for fd in funds_data}
    shm.add_daily_scores(today_str, daily_scores)
    
    # --- TREND_AVCISI Hesapla ---
    trend_avcisi_list = calculate_trend_avcisi(funds_data, decision_engine)
    
    # WhatsApp özeti (email için)
    whatsapp_summary = decision_engine.generate_report(results, mode="whatsapp", portfolio_funds=portfolio_funds)
    
    # TREND_AVCISI'yi WhatsApp summary'ye ekle
    if trend_avcisi_list:
        whatsapp_summary += "\n\n🎯 TREND_AVCISI - Top 5\n"
        for ta in trend_avcisi_list[:5]:
            whatsapp_summary += f"{ta['code']} — Δ{ta['delta']:+d} | RSI:{ta['rsi']:.0f} | ret5d:{ta['ret_5d']:.1f}%\n"
        if len(trend_avcisi_list) > 5:
            whatsapp_summary += f"  (+{len(trend_avcisi_list) - 5} daha)"
    else:
        history_days = shm.get_history_days()
        if history_days < 2:
            whatsapp_summary += f"\n\n🎯 TREND_AVCISI: Veri biriktiriliyor ({history_days}/3 gün)"
    
    # Konsola da yazdır
    print("\n" + "="*60)
    if trend_avcisi_list:
        print("🎯 TREND_AVCISI - Erken Trend Radarları (Top 5)")
        print("="*60)
        for ta in trend_avcisi_list[:5]:
            print(f"   {ta['code']:<6} | Δscore: {ta['delta']:+3d} | Score: {ta['score_final']:>2} | RSI: {ta['rsi']:.1f} | ret5d: {ta['ret_5d']:.1f}%")
        if len(trend_avcisi_list) > 5:
            print(f"   (+{len(trend_avcisi_list) - 5} daha)")
    else:
        history_days = shm.get_history_days()
        print(f"🎯 TREND_AVCISI: Veri biriktiriliyor ({history_days}/3 gün)")
    print("="*60)
    
    return results, html_file, {
        "sat": sat_count,
        "azalt": azalt_count,
        "al": al_count,
        "alinabilir": alinabilir_count,
        "tut": tut_count,
        "bekle": bekle_count,
        "alma": alma_count,
        "whatsapp": whatsapp_summary
    }


def send_decision_email(html_file: str, counts: dict):
    """Karar raporunu email olarak gönder"""
    email_reporter = EmailReporter()
    
    return email_reporter.send_decision_report_email(
        html_file=html_file,
        sat_count=counts.get("sat", 0),
        azalt_count=counts.get("azalt", 0),
        al_count=counts.get("al", 0),
        tut_count=counts.get("tut", 0),
        bekle_count=counts.get("bekle", 0),
        alma_count=counts.get("alma", 0),
        whatsapp_summary=counts.get("whatsapp", "")
    )


if __name__ == "__main__":
    import sys
    
    send_email = "--email" in sys.argv or "--mail" in sys.argv
    
    if "--full" in sys.argv:
        results, html_file, counts = run_full_decision_report()
        
        # Email gönder
        if send_email:
            print("\n📧 Email gönderiliyor...")
            send_decision_email(html_file, counts)
        
        # Raporu aç
        import subprocess
        subprocess.run(["open", html_file])
    elif "--whatsapp" in sys.argv:
        # Sadece WhatsApp formatında çıktı
        from decision_engine import DecisionEngine
        data_provider = FundDataProvider()
        technical_analyzer = TechnicalAnalyzer()
        panel_manager = PanelManager()
        decision_engine = DecisionEngine()
        
        panel_data = panel_manager.get_panel_data()
        portfolio_funds = panel_data.get('portfolio_funds', [])
        watch_funds = panel_data.get('watch_funds', [])
        target_funds = list(set(portfolio_funds + watch_funds))
        
        end_date = datetime.now().date().isoformat()
        start_date = (datetime.now() - timedelta(days=45)).date().isoformat()
        
        funds_data = []
        for fund_code in target_funds:
            try:
                fund_data = data_provider.get_fund_data(fund_code, start_date, end_date)
                if fund_data is None or len(fund_data) < 20:
                    continue
                analysis = technical_analyzer.analyze_fund(fund_data, fund_code)
                stats = get_fund_statistics(fund_data, fund_code)
                macd_yesterday = getattr(analysis, 'macd_yesterday', None)
                macd_signal_yesterday = getattr(analysis, 'macd_signal_yesterday', None)
                ret_5d = stats.get('pct_5d', 0) or 0
                
                funds_data.append({
                    "fund_code": fund_code,
                    "score": int(analysis.score),
                    "rsi": analysis.rsi,
                    "macd": analysis.macd,
                    "macd_signal": analysis.macd_signal,
                    "macd_yesterday": macd_yesterday,
                    "macd_signal_yesterday": macd_signal_yesterday,
                    "ret_5d": ret_5d,
                    "price": analysis.price,
                    "fund_statistics": stats
                })
            except:
                pass
        
        results = decision_engine.analyze_batch(funds_data, portfolio_funds=portfolio_funds)
        print(decision_engine.generate_report(results, mode="whatsapp", portfolio_funds=portfolio_funds))
    else:
        run_decision_report()
