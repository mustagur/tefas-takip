#!/usr/bin/env python3
"""
A/B Simülasyon Runner
daily_features JSON dosyasını kullanarak farklı eşik konfigürasyonlarını karşılaştırır

Kullanım:
    python run_threshold_simulation.py --input outputs/daily_features_2024-02-15.json
    python run_threshold_simulation.py --input outputs/daily_features_2024-02-15.json --html
"""

import json
import os
import sys
import argparse
from datetime import datetime
from decision_engine import DecisionEngine


# Konfigürasyonlar
CONFIGS = {
    "BASE": {
        "SCORE_TREND": 65,
        "SCORE_STRONG_TREND": 80,
        "SCORE_BREAKOUT": 80
    },
    "RELAXED": {
        "SCORE_TREND": 60,
        "SCORE_STRONG_TREND": 75,
        "SCORE_BREAKOUT": 75
    }
}


def load_features(input_file: str) -> dict:
    """Feature JSON dosyasını yükle"""
    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_simulation(features_data: dict, config_name: str, overrides: dict) -> dict:
    """Belirli bir konfigürasyon ile simülasyon çalıştır"""
    engine = DecisionEngine(overrides=overrides)
    portfolio = features_data.get("portfolio", [])
    funds = features_data.get("funds", [])
    
    # Features'ı decision engine formatına dönüştür
    funds_data = []
    for f in funds:
        funds_data.append({
            "fund_code": f["code"],
            "score": f["score"],
            "rsi": f["rsi"],
            "macd": f["macd"],
            "macd_signal": f["macd_signal"],
            "macd_yesterday": None,  # Features'da yok, hesaplayamıyoruz
            "macd_signal_yesterday": None,
            "ret_5d": f["ret_5d"],
            "fund_statistics": {}
        })
    
    # Analiz
    results = engine.analyze_batch(funds_data, portfolio_funds=portfolio)
    
    # Özet
    summary = {
        "SAT": 0, "AZALT": 0, "AL": 0, "ALINABİLİR ADAY": 0,
        "TUT": 0, "BEKLE": 0, "ALMA": 0
    }
    al_early = 0
    al_breakout = 0
    
    decisions_list = []
    for code, res in results.items():
        summary[res.decision.value] = summary.get(res.decision.value, 0) + 1
        if res.decision.value == "AL":
            if res.al_type == "EARLY":
                al_early += 1
            elif res.al_type == "BREAKOUT":
                al_breakout += 1
        
        # AL ve ALINABİLİR ADAY olanları listele
        if res.decision.value in ["AL", "ALINABİLİR ADAY"]:
            decisions_list.append({
                "code": code,
                "decision": res.decision.value,
                "reason": res.reason,
                "score_final": res.score_final,
                "rsi": res.rsi,
                "al_type": res.al_type
            })
    
    return {
        "config": config_name,
        "overrides": overrides,
        "summary": summary,
        "al_early": al_early,
        "al_breakout": al_breakout,
        "al_candidates": sorted(decisions_list, key=lambda x: x["score_final"], reverse=True)
    }


def compare_results(base_result: dict, relaxed_result: dict) -> dict:
    """İki sonucu karşılaştır"""
    comparison = {
        "base_summary": base_result["summary"],
        "relaxed_summary": relaxed_result["summary"],
        "differences": {}
    }
    
    for key in base_result["summary"]:
        base_val = base_result["summary"][key]
        relaxed_val = relaxed_result["summary"][key]
        if base_val != relaxed_val:
            comparison["differences"][key] = {
                "base": base_val,
                "relaxed": relaxed_val,
                "delta": relaxed_val - base_val
            }
    
    # Yeni AL adayları (relaxed'da var, base'de yok)
    base_codes = {x["code"] for x in base_result["al_candidates"]}
    relaxed_codes = {x["code"] for x in relaxed_result["al_candidates"]}
    
    new_in_relaxed = relaxed_codes - base_codes
    removed_in_relaxed = base_codes - relaxed_codes
    
    comparison["new_in_relaxed"] = [
        c for c in relaxed_result["al_candidates"] if c["code"] in new_in_relaxed
    ]
    comparison["removed_in_relaxed"] = [
        c for c in base_result["al_candidates"] if c["code"] in removed_in_relaxed
    ]
    
    return comparison


def generate_html_report(features_data: dict, base_result: dict, relaxed_result: dict, comparison: dict) -> str:
    """HTML karşılaştırma raporu oluştur"""
    date_str = features_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>A/B Simülasyon - {date_str}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h2 {{ margin-top: 0; color: #444; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f9f9f9; }}
        .highlight {{ background: #fffde7; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
        .badge {{ padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
        .badge-al {{ background: #c8e6c9; color: #2e7d32; }}
        .badge-aday {{ background: #bbdefb; color: #1565c0; }}
        .diff-section {{ margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 A/B Simülasyon Karşılaştırması</h1>
        <p>Tarih: {date_str} | Toplam Fon: {features_data.get('count', 0)}</p>
        
        <div class="grid">
            <div class="card">
                <h2>📊 BASE Konfigürasyon</h2>
                <p>SCORE_TREND={CONFIGS['BASE']['SCORE_TREND']}, SCORE_STRONG={CONFIGS['BASE']['SCORE_STRONG_TREND']}, SCORE_BREAKOUT={CONFIGS['BASE']['SCORE_BREAKOUT']}</p>
                <table>
                    <tr><th>Karar</th><th>Sayı</th></tr>
"""
    
    for key, val in base_result["summary"].items():
        html += f"                    <tr><td>{key}</td><td>{val}</td></tr>\n"
    
    html += f"""                </table>
                <p><strong>AL:</strong> {base_result['al_early']} Early + {base_result['al_breakout']} Breakout</p>
            </div>
            
            <div class="card">
                <h2>📊 RELAXED Konfigürasyon</h2>
                <p>SCORE_TREND={CONFIGS['RELAXED']['SCORE_TREND']}, SCORE_STRONG={CONFIGS['RELAXED']['SCORE_STRONG_TREND']}, SCORE_BREAKOUT={CONFIGS['RELAXED']['SCORE_BREAKOUT']}</p>
                <table>
                    <tr><th>Karar</th><th>Sayı</th></tr>
"""
    
    for key, val in relaxed_result["summary"].items():
        diff = ""
        if key in comparison["differences"]:
            delta = comparison["differences"][key]["delta"]
            diff = f" <span class='{'positive' if delta > 0 else 'negative'}'>(+{delta})</span>" if delta > 0 else f" <span class='negative'>({delta})</span>"
        html += f"                    <tr><td>{key}</td><td>{val}{diff}</td></tr>\n"
    
    html += f"""                </table>
                <p><strong>AL:</strong> {relaxed_result['al_early']} Early + {relaxed_result['al_breakout']} Breakout</p>
            </div>
        </div>
        
        <div class="diff-section">
            <div class="card">
                <h2>🆕 RELAXED'da Yeni Adaylar (BASE'de yok)</h2>
"""
    
    if comparison["new_in_relaxed"]:
        html += """                <table>
                    <tr><th>Kod</th><th>Karar</th><th>Score</th><th>RSI</th><th>Tip</th><th>Sebep</th></tr>
"""
        for c in comparison["new_in_relaxed"]:
            badge = "badge-al" if c["decision"] == "AL" else "badge-aday"
            html += f"""                    <tr>
                        <td><strong>{c['code']}</strong></td>
                        <td><span class="badge {badge}">{c['decision']}</span></td>
                        <td>{c['score_final']}</td>
                        <td>{c['rsi']:.1f}</td>
                        <td>{c['al_type'] or '-'}</td>
                        <td>{c['reason']}</td>
                    </tr>\n"""
        html += "                </table>\n"
    else:
        html += "                <p>Yeni aday yok</p>\n"
    
    html += """            </div>
        </div>
        
        <div class="diff-section">
            <div class="card">
                <h2>🔻 RELAXED'da Çıkan Adaylar (BASE'de var)</h2>
"""
    
    if comparison["removed_in_relaxed"]:
        html += """                <table>
                    <tr><th>Kod</th><th>Karar</th><th>Score</th><th>RSI</th></tr>
"""
        for c in comparison["removed_in_relaxed"]:
            html += f"""                    <tr>
                        <td><strong>{c['code']}</strong></td>
                        <td>{c['decision']}</td>
                        <td>{c['score_final']}</td>
                        <td>{c['rsi']:.1f}</td>
                    </tr>\n"""
        html += "                </table>\n"
    else:
        html += "                <p>Çıkan aday yok</p>\n"
    
    html += """            </div>
        </div>
    </div>
</body>
</html>"""
    
    return html


def print_single_profile_result(result: dict, config_name: str):
    """Tek profil sonucunu konsola yazdır"""
    print(f"\n{'='*50}")
    print(f"📊 {config_name} SONUÇLARI")
    print(f"{'='*50}")
    
    print(f"\n{'Karar':<20} {'Sayı':>8}")
    print("-"*30)
    for key, val in result["summary"].items():
        print(f"{key:<20} {val:>8}")
    
    print(f"\n📈 AL Dağılımı: {result['al_early']} Early + {result['al_breakout']} Breakout")
    
    if result["al_candidates"]:
        print(f"\n✅ AL/ADAY Listesi ({len(result['al_candidates'])} adet):")
        for c in result["al_candidates"]:
            print(f"   {c['code']:<6} | {c['decision']:<15} | Score: {c['score_final']:>3} | RSI: {c['rsi']:.1f} | {c['reason']}")


def main():
    parser = argparse.ArgumentParser(description="A/B Threshold Simulation Runner")
    parser.add_argument("--input", "-i", required=True, help="daily_features JSON dosyası")
    parser.add_argument("--profile", "-p", choices=["base", "relaxed"], help="Tek profil çalıştır (base veya relaxed)")
    parser.add_argument("--html", action="store_true", help="HTML rapor da oluştur")
    parser.add_argument("--output", "-o", help="Çıktı dizini (varsayılan: outputs/)")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ Dosya bulunamadı: {args.input}")
        sys.exit(1)
    
    output_dir = args.output or os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Verileri yükle
    features_data = load_features(args.input)
    date_str = features_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    print(f"\n📁 Girdi: {args.input}")
    print(f"📅 Tarih: {date_str}")
    print(f"📊 Fon sayısı: {features_data.get('count', 0)}")
    
    # Tek profil modu
    if args.profile:
        config_name = args.profile.upper()
        config = CONFIGS[config_name]
        
        print(f"\n⚙️ {config_name} profili çalıştırılıyor...")
        print(f"   Config: SCORE_TREND={config['SCORE_TREND']}, SCORE_STRONG={config['SCORE_STRONG_TREND']}, SCORE_BREAKOUT={config['SCORE_BREAKOUT']}")
        
        result = run_simulation(features_data, config_name, config)
        print_single_profile_result(result, config_name)
        
        # JSON kaydet
        result_file = os.path.join(output_dir, f"simulation_{config_name.lower()}_{date_str}.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                "date": date_str,
                "profile": config_name,
                "config": config,
                "summary": result["summary"],
                "al_early": result["al_early"],
                "al_breakout": result["al_breakout"],
                "al_candidates": result["al_candidates"]
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 Sonuç: {result_file}")
        print("\n✅ Simülasyon tamamlandı!")
        return
    
    # A/B Karşılaştırma modu (varsayılan)
    print(f"\n🔬 A/B Simülasyon Başlatılıyor...")
    
    # BASE simülasyonu
    print(f"\n⚙️ BASE konfigürasyon çalıştırılıyor...")
    base_result = run_simulation(features_data, "BASE", CONFIGS["BASE"])
    print(f"   AL: {base_result['summary'].get('AL', 0)} | ADAY: {base_result['summary'].get('ALINABİLİR ADAY', 0)}")
    
    # RELAXED simülasyonu
    print(f"\n⚙️ RELAXED konfigürasyon çalıştırılıyor...")
    relaxed_result = run_simulation(features_data, "RELAXED", CONFIGS["RELAXED"])
    print(f"   AL: {relaxed_result['summary'].get('AL', 0)} | ADAY: {relaxed_result['summary'].get('ALINABİLİR ADAY', 0)}")
    
    # Karşılaştır
    comparison = compare_results(base_result, relaxed_result)
    
    # Özet JSON
    summary_file = os.path.join(output_dir, f"compare_summary_{date_str}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "date": date_str,
            "base": {
                "config": CONFIGS["BASE"],
                "summary": base_result["summary"],
                "al_early": base_result["al_early"],
                "al_breakout": base_result["al_breakout"],
                "al_candidates": base_result["al_candidates"]
            },
            "relaxed": {
                "config": CONFIGS["RELAXED"],
                "summary": relaxed_result["summary"],
                "al_early": relaxed_result["al_early"],
                "al_breakout": relaxed_result["al_breakout"],
                "al_candidates": relaxed_result["al_candidates"]
            },
            "comparison": {
                "differences": comparison["differences"],
                "new_in_relaxed": comparison["new_in_relaxed"],
                "removed_in_relaxed": comparison["removed_in_relaxed"]
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 Özet: {summary_file}")
    
    # HTML rapor (opsiyonel)
    if args.html:
        html_content = generate_html_report(features_data, base_result, relaxed_result, comparison)
        html_file = os.path.join(output_dir, f"compare_report_{date_str}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"📄 HTML Rapor: {html_file}")
    
    # Konsol özeti
    print("\n" + "="*50)
    print("📊 KARŞILAŞTIRMA ÖZETİ")
    print("="*50)
    print(f"\n{'Karar':<20} {'BASE':>8} {'RELAXED':>8} {'Delta':>8}")
    print("-"*50)
    for key in base_result["summary"]:
        b = base_result["summary"][key]
        r = relaxed_result["summary"][key]
        delta = r - b
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        print(f"{key:<20} {b:>8} {r:>8} {delta_str:>8}")
    
    if comparison["new_in_relaxed"]:
        print(f"\n🆕 RELAXED'da {len(comparison['new_in_relaxed'])} yeni aday:")
        for c in comparison["new_in_relaxed"][:5]:
            print(f"   {c['code']} ({c['decision']}) - Score: {c['score_final']}")
    
    print("\n✅ Simülasyon tamamlandı!")


if __name__ == "__main__":
    main()
