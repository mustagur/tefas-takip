#!/usr/bin/env python3
"""
Score History Manager
Günlük score verilerini saklar ve delta hesaplar
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "score_history.json")
MAX_DAYS = 10  # Son 10 günü tut (gereksiz büyümeyi önle)


def load_history() -> Dict:
    """Geçmiş verileri yükle"""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_updated": None, "history": {}}


def save_history(data: Dict):
    """Geçmiş verileri kaydet"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_daily_scores(date_str: str, scores: Dict[str, int]):
    """
    Günlük score'ları ekle
    
    Args:
        date_str: Tarih (YYYY-MM-DD format)
        scores: {fund_code: score} dict
    """
    data = load_history()
    
    # Bugünü ekle
    data["history"][date_str] = scores
    data["last_updated"] = date_str
    
    # Eski verileri temizle (MAX_DAYS'den eski)
    cutoff_date = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=MAX_DAYS)).strftime("%Y-%m-%d")
    data["history"] = {
        d: s for d, s in data["history"].items() 
        if d >= cutoff_date
    }
    
    save_history(data)
    print(f"📊 Score history güncellendi: {date_str} ({len(scores)} fon)")


def get_score_delta(fund_code: str, days: int = 3) -> Optional[int]:
    """
    Belirtilen gün önceki score ile bugünkü score arasındaki farkı hesapla
    
    Args:
        fund_code: Fon kodu
        days: Kaç gün öncesiyle karşılaştırılacak (varsayılan 3)
    
    Returns:
        delta_score veya None (yeterli veri yoksa)
    """
    data = load_history()
    history = data.get("history", {})
    
    if len(history) < 2:
        return None
    
    # Tarihleri sırala (en yeni en sonda)
    sorted_dates = sorted(history.keys())
    
    if len(sorted_dates) < 2:
        return None
    
    # En son tarih (bugün)
    today = sorted_dates[-1]
    today_score = history[today].get(fund_code)
    
    if today_score is None:
        return None
    
    # N gün önceki tarihi bul
    target_idx = max(0, len(sorted_dates) - 1 - days)
    target_date = sorted_dates[target_idx]
    target_score = history[target_date].get(fund_code)
    
    if target_score is None:
        return None
    
    return today_score - target_score


def get_all_deltas(days: int = 3) -> Dict[str, int]:
    """
    Tüm fonların delta_score değerlerini hesapla
    
    Returns:
        {fund_code: delta_score} dict
    """
    data = load_history()
    history = data.get("history", {})
    
    if len(history) < 2:
        return {}
    
    sorted_dates = sorted(history.keys())
    
    if len(sorted_dates) < 2:
        return {}
    
    today = sorted_dates[-1]
    target_idx = max(0, len(sorted_dates) - 1 - days)
    target_date = sorted_dates[target_idx]
    
    today_scores = history[today]
    target_scores = history[target_date]
    
    deltas = {}
    for code, score in today_scores.items():
        if code in target_scores:
            deltas[code] = score - target_scores[code]
    
    return deltas


def get_history_days() -> int:
    """Kaç günlük veri var"""
    data = load_history()
    return len(data.get("history", {}))


def get_date_range() -> tuple:
    """Veri aralığını döndür (min_date, max_date)"""
    data = load_history()
    history = data.get("history", {})
    if not history:
        return (None, None)
    dates = sorted(history.keys())
    return (dates[0], dates[-1])


if __name__ == "__main__":
    # Test
    print(f"📅 Kayıtlı gün sayısı: {get_history_days()}")
    date_range = get_date_range()
    if date_range[0]:
        print(f"📆 Tarih aralığı: {date_range[0]} → {date_range[1]}")
    
    # Örnek delta
    deltas = get_all_deltas(3)
    if deltas:
        top_5 = sorted(deltas.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n🚀 En çok yükselen 5 fon (3g delta):")
        for code, delta in top_5:
            print(f"   {code}: +{delta}")
