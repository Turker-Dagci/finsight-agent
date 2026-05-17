import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger("cashflow_forecast")

def forecast_cashflow(
    parsed_summary: dict,
    categories: dict,
    predicted_expenses: dict,
    gun_sayisi: int = 30
) -> dict:
    """
    30 günlük nakit akış tahmini.
    Mevcut tasarruf + beklenen giderler = ay sonu tahmini bakiye.
    """
    bugun = datetime.now()
    ayin_kalan_gunu = gun_sayisi - bugun.day

    gelir = parsed_summary.get("toplam_gelir", 0) or 0
    gider = parsed_summary.get("toplam_gider", 0) or 0
    gunluk_ortalama_gider = gider / 30 if gider > 0 else 0

    # Kalan günlük gider tahmini
    kalan_gun_gider = gunluk_ortalama_gider * ayin_kalan_gunu

    # Sabit giderler (öngörülen)
    sabit_giderler = predicted_expenses.get("toplam", 0) if predicted_expenses else 0

    # Mevcut tasarruf (ay başından bugüne)
    gecen_gun = bugun.day
    bugun_itibariyle_gelir = gelir
    bugun_itibariyle_gider = gunluk_ortalama_gider * gecen_gun
    mevcut_nakit = bugun_itibariyle_gelir - bugun_itibariyle_gider

    # Ay sonu tahmini
    ay_sonu_tahmini = mevcut_nakit - kalan_gun_gider

    # Risk seviyesi
    if ay_sonu_tahmini >= gelir * 0.2:
        risk = "düşük"
        risk_mesaj = "Ay sonunda iyi bir tasarruf bekleniyor."
        risk_renk = "success"
    elif ay_sonu_tahmini >= gelir * 0.05:
        risk = "orta"
        risk_mesaj = "Ay sonunda sınırda bir bakiye bekleniyor."
        risk_renk = "warning"
    elif ay_sonu_tahmini >= 0:
        risk = "yüksek"
        risk_mesaj = "Dikkat: Ay sonunda nakit çok azalabilir."
        risk_renk = "warning"
    else:
        risk = "kritik"
        risk_mesaj = "Uyarı: Mevcut hızla ay sonunda nakit açığı oluşabilir."
        risk_renk = "error"

    # Günlük güvenli harcama limiti
    if ayin_kalan_gunu > 0:
        gunluk_limit = max(
            (mevcut_nakit - sabit_giderler) / ayin_kalan_gunu, 0
        )
    else:
        gunluk_limit = 0

    logger.info(
        f"Nakit akış tahmini: ay sonu {ay_sonu_tahmini:,.0f} TL — risk: {risk}"
    )

    return {
        "bugun": bugun.strftime("%d %B %Y"),
        "ayin_kalan_gunu": ayin_kalan_gunu,
        "mevcut_nakit": round(mevcut_nakit, 0),
        "kalan_gun_gider_tahmini": round(kalan_gun_gider, 0),
        "sabit_giderler": round(sabit_giderler, 0),
        "ay_sonu_tahmini": round(ay_sonu_tahmini, 0),
        "gunluk_guvenli_limit": round(gunluk_limit, 0),
        "risk": risk,
        "risk_mesaj": risk_mesaj,
        "risk_renk": risk_renk,
        "gunluk_ortalama_gider": round(gunluk_ortalama_gider, 0),
    }


if __name__ == "__main__":
    test_summary = {"toplam_gelir": 42000.0, "toplam_gider": 35994.46}
    test_predicted = {"toplam": 13986.0}

    result = forecast_cashflow(
        parsed_summary=test_summary,
        categories={"kira": 12000, "gida": 5411},
        predicted_expenses=test_predicted
    )

    print(f"\nNakit Akış Tahmini — {result['bugun']}")
    print(f"Ayın kalan günü    : {result['ayin_kalan_gunu']} gün")
    print(f"Mevcut nakit       : {result['mevcut_nakit']:,.0f} TL")
    print(f"Sabit giderler     : {result['sabit_giderler']:,.0f} TL")
    print(f"Ay sonu tahmini    : {result['ay_sonu_tahmini']:,.0f} TL")
    print(f"Günlük limit       : {result['gunluk_guvenli_limit']:,.0f} TL/gün")
    print(f"Risk               : {result['risk'].upper()}")
    print(f"Mesaj              : {result['risk_mesaj']}")