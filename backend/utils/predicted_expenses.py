import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger("predicted_expenses")

# Bilinen sabit gider kalıpları
SABIT_GIDERLER = {
    "kira": {"gun": 1, "aciklama": "Kira Ödemesi"},
    "elektrik": {"gun": 8, "aciklama": "Elektrik Faturası"},
    "dogalgaz": {"gun": 10, "aciklama": "Doğalgaz Faturası"},
    "su": {"gun": 12, "aciklama": "Su Faturası"},
    "internet": {"gun": 15, "aciklama": "İnternet Faturası"},
    "telefon": {"gun": 20, "aciklama": "Telefon Faturası"},
}

ABONE_KEYWORDS = {
    "netflix": {"gun": 4, "aciklama": "Netflix Abonelik"},
    "spotify": {"gun": 4, "aciklama": "Spotify Abonelik"},
    "amazon": {"gun": 5, "aciklama": "Amazon Prime"},
    "apple": {"gun": 6, "aciklama": "Apple Abonelik"},
    "youtube": {"gun": 7, "aciklama": "YouTube Premium"},
}

def predict_upcoming_expenses(
    transactions: list,
    categories: dict,
    subscriptions: list,
    gun_sayisi: int = 30
) -> dict:
    """
    Mevcut işlem geçmişinden gelecek 30 günlük
    zorunlu ve tekrar eden giderleri tahmin eder.
    """
    bugun = datetime.now()
    bitis = bugun + timedelta(days=gun_sayisi)
    tahminler = []

    # Aboneliklerden gelen tahminler
    for abone in subscriptions:
        aciklama = abone.get("aciklama", "").lower()
        tutar = abone.get("tutar", 0)

        for keyword, bilgi in ABONE_KEYWORDS.items():
            if keyword in aciklama:
                tahmin_gun = bugun.replace(day=bilgi["gun"])
                if tahmin_gun < bugun:
                    tahmin_gun = tahmin_gun.replace(
                        month=tahmin_gun.month + 1
                        if tahmin_gun.month < 12 else 1
                    )
                if bugun <= tahmin_gun <= bitis:
                    tahminler.append({
                        "tarih": tahmin_gun.strftime("%d %B"),
                        "aciklama": bilgi["aciklama"],
                        "tutar": round(tutar, 0),
                        "tur": "abonelik",
                        "kesinlik": "yüksek"
                    })
                break

    # Kategori bazlı sabit gider tahminleri
    for kategori, bilgi in SABIT_GIDERLER.items():
        if kategori in ["kira"] and categories.get("kira", 0) > 0:
            tahmin_gun = bugun.replace(day=bilgi["gun"])
            if tahmin_gun < bugun:
                if bugun.month < 12:
                    tahmin_gun = tahmin_gun.replace(month=bugun.month + 1)
                else:
                    tahmin_gun = tahmin_gun.replace(year=bugun.year + 1, month=1)
            if bugun <= tahmin_gun <= bitis:
                tahminler.append({
                    "tarih": tahmin_gun.strftime("%d %B"),
                    "aciklama": bilgi["aciklama"],
                    "tutar": round(categories.get("kira", 0), 0),
                    "tur": "zorunlu",
                    "kesinlik": "yüksek"
                })

        elif kategori == "elektrik" and categories.get("fatura", 0) > 0:
            fatura_tahmini = categories.get("fatura", 0) * 0.4
            tahmin_gun = bugun.replace(day=bilgi["gun"])
            if tahmin_gun < bugun:
                if bugun.month < 12:
                    tahmin_gun = tahmin_gun.replace(month=bugun.month + 1)
                else:
                    tahmin_gun = tahmin_gun.replace(year=bugun.year + 1, month=1)
            if bugun <= tahmin_gun <= bitis:
                tahminler.append({
                    "tarih": tahmin_gun.strftime("%d %B"),
                    "aciklama": bilgi["aciklama"],
                    "tutar": round(fatura_tahmini, 0),
                    "tur": "zorunlu",
                    "kesinlik": "orta"
                })

    # Tarihe göre sırala
    tahminler.sort(key=lambda x: x["tarih"])

    toplam_tahmin = sum(t["tutar"] for t in tahminler)

    logger.info(f"{len(tahminler)} öngörülen gider, toplam {toplam_tahmin:,.0f} TL")

    return {
        "tahminler": tahminler,
        "toplam": round(toplam_tahmin, 0),
        "gun_sayisi": gun_sayisi,
        "bitis_tarihi": bitis.strftime("%d %B %Y")
    }


if __name__ == "__main__":
    test_subscriptions = [
        {"aciklama": "Netflix Abonelik", "tutar": 349.99},
        {"aciklama": "Spotify Abonelik", "tutar": 99.99},
    ]
    test_categories = {
        "kira": 12000.0,
        "fatura": 3840.0,
    }

    result = predict_upcoming_expenses(
        transactions=[],
        categories=test_categories,
        subscriptions=test_subscriptions
    )

    print(f"\nÖnümüzdeki {result['gun_sayisi']} gün ({result['bitis_tarihi']})")
    print(f"Toplam beklenen gider: {result['toplam']:,.0f} TL")
    print("\nDetay:")
    for t in result["tahminler"]:
        print(f"  {t['tarih']:10} | {t['aciklama']:25} | {t['tutar']:>8,.0f} TL | {t['kesinlik']}")