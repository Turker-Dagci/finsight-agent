import json
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
logger = setup_logger("analyst_agent")

from google import genai
from google.genai import types as genai_types
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

# ── Türkiye kategori bazlı enflasyon (TÜİK Nisan 2026 tahmini) ──
INFLATION_DATA = {
    "gida":     {"aylik": 3.2,  "yillik": 48.5},
    "ulasim":   {"aylik": 4.1,  "yillik": 61.2},
    "fatura":   {"aylik": 5.8,  "yillik": 78.4},
    "eglence":  {"aylik": 2.9,  "yillik": 38.7},
    "saglik":   {"aylik": 3.6,  "yillik": 52.1},
    "kira":     {"aylik": 6.2,  "yillik": 89.3},
    "diger":    {"aylik": 3.4,  "yillik": 45.0},
}

# ── Türkiye vergi oranları ──────────────────────────────────────
TAX_RATES = {
    "gida":    {"kdv": 0.10, "otv": 0.00},
    "ulasim":  {"kdv": 0.20, "otv": 0.68},
    "fatura":  {"kdv": 0.20, "otv": 0.00},
    "eglence": {"kdv": 0.20, "otv": 0.00},
    "saglik":  {"kdv": 0.10, "otv": 0.00},
    "kira":    {"kdv": 0.00, "otv": 0.00},
    "maas":    {"kdv": 0.00, "otv": 0.00},
    "diger":   {"kdv": 0.20, "otv": 0.00},
}

def categorize_transactions(transactions: list) -> dict:
    """İşlemleri kategorilere göre toplar."""
    categories = {}
    for t in transactions:
        if t.get("tur") == "gelir":
            continue
        kategori = t.get("kategori", "diger")
        tutar = abs(t.get("tutar", 0))
        categories[kategori] = categories.get(kategori, 0) + tutar
    return categories

def calculate_inflation_impact(categories: dict) -> dict:
    """Her kategori için enflasyon düzeltmeli analiz üretir."""
    result = {}
    for kategori, tutar in categories.items():
        inf = INFLATION_DATA.get(kategori, INFLATION_DATA["diger"])
        reel_deger = tutar / (1 + inf["aylik"] / 100)
        result[kategori] = {
            "nominal": round(tutar, 2),
            "reel": round(reel_deger, 2),
            "kayip": round(tutar - reel_deger, 2),
            "aylik_enflasyon": inf["aylik"],
            "yillik_enflasyon": inf["yillik"],
        }
    return result

def calculate_tax_breakdown(categories: dict) -> dict:
    """Harcamalardaki gizli vergi yükünü hesaplar."""
    result = {}
    toplam_vergi = 0

    for kategori, tutar in categories.items():
        rates = TAX_RATES.get(kategori, TAX_RATES["diger"])
        kdv_tutari = tutar * rates["kdv"] / (1 + rates["kdv"]) if rates["kdv"] > 0 else 0
        otv_tutari = tutar * rates["otv"] / (1 + rates["otv"]) if rates["otv"] > 0 else 0
        toplam = kdv_tutari + otv_tutari
        toplam_vergi += toplam

        result[kategori] = {
            "harcama": round(tutar, 2),
            "kdv": round(kdv_tutari, 2),
            "otv": round(otv_tutari, 2),
            "toplam_vergi": round(toplam, 2),
        }

    result["TOPLAM"] = {
        "toplam_vergi": round(toplam_vergi, 2),
    }
    return result

def detect_anomalies(transactions: list) -> list:
    """Tekrar eden ödemeleri ve olağandışı harcamaları tespit eder."""
    anomalies = []
    aciklama_sayac = {}

    for t in transactions:
        if t.get("tur") == "gelir":
            continue
        aciklama = t.get("aciklama", "").lower()
        aciklama_sayac[aciklama] = aciklama_sayac.get(aciklama, 0) + 1

    for aciklama, sayi in aciklama_sayac.items():
        if sayi > 1:
            anomalies.append(f"'{aciklama}' bu dönemde {sayi} kez tekrarlandı — olası mükerrer ödeme.")

    return anomalies

def detect_subscriptions(transactions: list) -> list:
    """Abonelikleri tespit eder."""
    abone_keywords = ["netflix", "spotify", "amazon", "apple", "youtube",
                      "disney", "exxen", "gain", "blutv", "abonelik"]
    subscriptions = []

    for t in transactions:
        aciklama = t.get("aciklama", "").lower()
        if any(k in aciklama for k in abone_keywords):
            subscriptions.append({
                "aciklama": t.get("aciklama"),
                "tutar": abs(t.get("tutar", 0)),
                "tarih": t.get("tarih"),
            })

    return subscriptions

def run_analyst(transactions: list, parsed_summary: dict) -> dict:
    logger.info("Kategorilendirme başladı")
    categories = categorize_transactions(transactions)

    logger.info("Enflasyon analizi başladı")
    inflation = calculate_inflation_impact(categories)

    logger.info("Vergi X-Ray hesaplanıyor")
    tax = calculate_tax_breakdown(categories)

    logger.info("Anomali tespiti başladı")
    anomalies = detect_anomalies(transactions)

    logger.info("Abonelik tespiti başladı")
    subscriptions = detect_subscriptions(transactions)

    # Davranışsal koçluk — bu satır eksikti
    behavioral_insights = generate_behavioral_insights(transactions, categories)

    toplam_gider = sum(categories.values())
    toplam_gelir = parsed_summary.get("toplam_gelir", 0)

    return {
        "categories": categories,
        "inflation_analysis": inflation,
        "tax_breakdown": tax,
        "anomalies": anomalies,
        "subscriptions": subscriptions,
        "behavioral_insights": behavioral_insights,
        "ozet": {
            "toplam_gelir": toplam_gelir,
            "toplam_gider": round(toplam_gider, 2),
            "net": round(toplam_gelir - toplam_gider, 2),
            "tasarruf_orani": round((toplam_gelir - toplam_gider) / toplam_gelir * 100, 1) if toplam_gelir > 0 else 0,
            "toplam_vergi": tax.get("TOPLAM", {}).get("toplam_vergi", 0),
        }
    }

def generate_behavioral_insights(transactions: list, categories: dict) -> list:
    """
    Kullanıcının harcama davranışlarını analiz eder.
    'Bu ay 4 kez Starbucks'a gittin' tarzı uyarılar üretir.
    """
    insights = []

    # Yer bazlı tekrar analizi
    yer_sayac = {}
    for t in transactions:
        if t.get("tur") == "gelir":
            continue
        aciklama = t.get("aciklama", "").lower()
        tutar = abs(t.get("tutar", 0))
        yer_sayac[aciklama] = yer_sayac.get(aciklama, {"sayi": 0, "toplam": 0})
        yer_sayac[aciklama]["sayi"] += 1
        yer_sayac[aciklama]["toplam"] += tutar

    for yer, veri in yer_sayac.items():
        if veri["sayi"] >= 3:
            insights.append(
                f"☕ '{yer.title()}' bu ay {veri['sayi']} kez ziyaret edildi "
                f"— toplam {veri['toplam']:,.0f} TL."
            )

    # ATM nakit çekimi
    atm_toplam = sum(
        abs(t.get("tutar", 0)) for t in transactions
        if "atm" in t.get("aciklama", "").lower()
        and t.get("tur") == "gider"
    )
    if atm_toplam > 0:
        insights.append(
            f"💵 Bu ay ATM'den toplam {atm_toplam:,.0f} TL nakit çekildi. "
            f"Nakit harcamalar takip edilemiyor — dijital ödeme tercih edin."
        )

    # Hafta sonu harcama analizi
    hafta_sonu_toplam = 0
    hafta_ici_toplam = 0
    for t in transactions:
        if t.get("tur") == "gelir":
            continue
        try:
            from datetime import datetime
            tarih = datetime.strptime(t.get("tarih", ""), "%Y-%m-%d")
            tutar = abs(t.get("tutar", 0))
            if tarih.weekday() >= 5:
                hafta_sonu_toplam += tutar
            else:
                hafta_ici_toplam += tutar
        except Exception:
            pass

    if hafta_sonu_toplam > 0 and hafta_ici_toplam > 0:
        oran = hafta_sonu_toplam / (hafta_sonu_toplam + hafta_ici_toplam) * 100
        if oran > 40:
            insights.append(
                f"📅 Harcamanın %{oran:.0f}'i hafta sonlarında gerçekleşti "
                f"({hafta_sonu_toplam:,.0f} TL). "
                f"Hafta sonu planlaması bütçeni etkileyebilir."
            )

    # Eğlence kategorisi yüksekse
    eglence = categories.get("eglence", 0)
    toplam = sum(categories.values())
    if toplam > 0 and eglence / toplam > 0.15:
        insights.append(
            f"🎮 Eğlence harcaman toplam giderin %{eglence/toplam*100:.0f}'i "
            f"({eglence:,.0f} TL). Kısılabilir en esnek kategori bu."
        )

    return insights


if __name__ == "__main__":
    # Demo verisiyle test
    test_transactions = [
        {"tarih": "2026-04-01", "aciklama": "Maaş Ödemesi", "tutar": 42000.0, "tur": "gelir", "kategori": "maas"},
        {"tarih": "2026-04-02", "aciklama": "Migros Market", "tutar": -1240.5, "tur": "gider", "kategori": "gida"},
        {"tarih": "2026-04-03", "aciklama": "Shell Yakıt", "tutar": -1850.0, "tur": "gider", "kategori": "ulasim"},
        {"tarih": "2026-04-04", "aciklama": "Netflix Abonelik", "tutar": -349.99, "tur": "gider", "kategori": "eglence"},
        {"tarih": "2026-04-08", "aciklama": "BEDAŞ Elektrik", "tutar": -2340.0, "tur": "gider", "kategori": "fatura"},
        {"tarih": "2026-04-12", "aciklama": "Opet Yakıt", "tutar": -1650.0, "tur": "gider", "kategori": "ulasim"},
        {"tarih": "2026-04-20", "aciklama": "Netflix Abonelik", "tutar": -349.99, "tur": "gider", "kategori": "eglence"},
        {"tarih": "2026-04-25", "aciklama": "Kira Ödemesi", "tutar": -12000.0, "tur": "gider", "kategori": "kira"},
    ]

    test_summary = {"toplam_gelir": 42000.0, "toplam_gider": 19780.48}

    result = run_analyst(test_transactions, test_summary)

    print("\n--- KATEGORİLER ---")
    for k, v in result["categories"].items():
        print(f"  {k:12} : {v:>10.2f} TL")

    print("\n--- ENFLASYON ANALİZİ ---")
    for k, v in result["inflation_analysis"].items():
        print(f"  {k:12} : nominal {v['nominal']:>8.2f} TL | reel {v['reel']:>8.2f} TL | kayıp {v['kayip']:>6.2f} TL")

    print("\n--- VERGİ X-RAY ---")
    print(f"  Toplam gizli vergi: {result['tax_breakdown']['TOPLAM']['toplam_vergi']:.2f} TL")

    print("\n--- ANOMALİLER ---")
    for a in result["anomalies"]:
        print(f"  ⚠ {a}")

    print("\n--- ABONELİKLER ---")
    for s in result["subscriptions"]:
        print(f"  {s['aciklama']:30} : {s['tutar']:.2f} TL")

    print("\n--- ÖZET ---")
    for k, v in result["ozet"].items():
        print(f"  {k:20} : {v}")