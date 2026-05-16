import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger

logger = setup_logger("health_score")

def calculate_health_score(
    parsed_summary: dict,
    categories: dict,
    inflation_analysis: dict,
    subscriptions: list,
    anomalies: list
) -> dict:
    """
    Finansal sağlık skoru hesaplar — 100 üzerinden.
    
    Bileşenler:
    - Tasarruf oranı    : 30 puan
    - Enflasyon direnci : 25 puan
    - Abonelik sağlığı  : 20 puan
    - Anomali durumu    : 15 puan
    - Bütçe dengesi     : 10 puan
    """
    toplam_gelir = parsed_summary.get("toplam_gelir", 0)
    toplam_gider = parsed_summary.get("toplam_gider", 0)
    puan = {}
    detay = {}

    # ── 1. Tasarruf Oranı (30 puan) ──────────────────────────
    if toplam_gelir > 0:
        tasarruf_orani = (toplam_gelir - toplam_gider) / toplam_gelir * 100
    else:
        tasarruf_orani = 0

    if tasarruf_orani >= 30:
        puan["tasarruf"] = 30
        detay["tasarruf"] = "Mükemmel tasarruf oranı"
    elif tasarruf_orani >= 20:
        puan["tasarruf"] = 24
        detay["tasarruf"] = "İyi tasarruf oranı"
    elif tasarruf_orani >= 10:
        puan["tasarruf"] = 15
        detay["tasarruf"] = "Geliştirilmeli"
    elif tasarruf_orani >= 0:
        puan["tasarruf"] = 7
        detay["tasarruf"] = "Kritik — tasarruf çok düşük"
    else:
        puan["tasarruf"] = 0
        detay["tasarruf"] = "Tehlikeli — gider geliri aşıyor"

    # ── 2. Enflasyon Direnci (25 puan) ───────────────────────
    if inflation_analysis:
        yuksek_enflasyon_kategori = sum(
            1 for v in inflation_analysis.values()
            if v.get("yillik_enflasyon", 0) > 60
            and v.get("nominal", 0) > 2000
        )

        if yuksek_enflasyon_kategori == 0:
            puan["enflasyon"] = 25
            detay["enflasyon"] = "Enflasyona karşı iyi konum"
        elif yuksek_enflasyon_kategori == 1:
            puan["enflasyon"] = 18
            detay["enflasyon"] = "1 yüksek enflasyon kategorisi"
        elif yuksek_enflasyon_kategori == 2:
            puan["enflasyon"] = 10
            detay["enflasyon"] = "2 yüksek enflasyon kategorisi"
        else:
            puan["enflasyon"] = 3
            detay["enflasyon"] = "Birden fazla kritik kategori"
    else:
        puan["enflasyon"] = 12
        detay["enflasyon"] = "Veri yetersiz"

    # ── 3. Abonelik Sağlığı (20 puan) ────────────────────────
    toplam_abone = sum(s.get("tutar", 0) for s in subscriptions)
    if toplam_gelir > 0:
        abone_orani = toplam_abone / toplam_gelir * 100
    else:
        abone_orani = 0

    if abone_orani == 0:
        puan["abonelik"] = 20
        detay["abonelik"] = "Abonelik yok"
    elif abone_orani < 3:
        puan["abonelik"] = 18
        detay["abonelik"] = "Abonelik oranı sağlıklı"
    elif abone_orani < 7:
        puan["abonelik"] = 12
        detay["abonelik"] = "Abonelik oranı normal"
    elif abone_orani < 15:
        puan["abonelik"] = 6
        detay["abonelik"] = "Abonelik yükü yüksek"
    else:
        puan["abonelik"] = 0
        detay["abonelik"] = "Kritik abonelik yükü"

    # ── 4. Anomali Durumu (15 puan) ───────────────────────────
    anomali_sayisi = len(anomalies)

    if anomali_sayisi == 0:
        puan["anomali"] = 15
        detay["anomali"] = "Anomali tespit edilmedi"
    elif anomali_sayisi == 1:
        puan["anomali"] = 10
        detay["anomali"] = "1 anomali tespit edildi"
    elif anomali_sayisi <= 3:
        puan["anomali"] = 5
        detay["anomali"] = f"{anomali_sayisi} anomali tespit edildi"
    else:
        puan["anomali"] = 0
        detay["anomali"] = "Çok sayıda anomali"

    # ── 5. Bütçe Dengesi (10 puan) ────────────────────────────
    if categories and toplam_gelir > 0:
        kira = categories.get("kira", 0)
        kira_orani = kira / toplam_gelir * 100

        if kira_orani == 0:
            puan["butce"] = 10
            detay["butce"] = "Kira gideri yok"
        elif kira_orani <= 30:
            puan["butce"] = 10
            detay["butce"] = "Kira oranı sağlıklı"
        elif kira_orani <= 40:
            puan["butce"] = 6
            detay["butce"] = "Kira oranı yüksek"
        else:
            puan["butce"] = 2
            detay["butce"] = "Kira oranı kritik"
    else:
        puan["butce"] = 5
        detay["butce"] = "Veri yetersiz"

    # ── Toplam ────────────────────────────────────────────────
    toplam = sum(puan.values())

    if toplam >= 85:
        seviye = "Mükemmel"
        renk = "green"
        mesaj = "Finansal sağlığınız çok iyi durumda."
    elif toplam >= 70:
        seviye = "İyi"
        renk = "blue"
        mesaj = "Finansal durumunuz genel olarak sağlıklı."
    elif toplam >= 50:
        seviye = "Orta"
        renk = "orange"
        mesaj = "Bazı alanlarda iyileştirme yapılabilir."
    elif toplam >= 30:
        seviye = "Zayıf"
        renk = "red"
        mesaj = "Finansal durumunuz dikkat gerektiriyor."
    else:
        seviye = "Kritik"
        renk = "darkred"
        mesaj = "Acil finansal düzenleme gerekli."

    logger.info(f"Finansal sağlık skoru: {toplam}/100 — {seviye}")

    return {
        "toplam_skor": toplam,
        "seviye": seviye,
        "renk": renk,
        "mesaj": mesaj,
        "bilesenler": puan,
        "detay": detay,
        "tasarruf_orani": round(tasarruf_orani, 1),
        "abone_orani": round(abone_orani, 1),
    }


if __name__ == "__main__":
    test_summary = {"toplam_gelir": 42000.0, "toplam_gider": 35994.46}
    test_categories = {"gida": 5411.5, "ulasim": 6450.0, "kira": 12000.0}
    test_inflation = {
        "ulasim": {"yillik_enflasyon": 61.2, "nominal": 6450.0},
        "kira":   {"yillik_enflasyon": 89.3, "nominal": 12000.0},
    }
    test_subscriptions = [
        {"tutar": 349.99},
        {"tutar": 99.99},
        {"tutar": 299.99},
    ]
    test_anomalies = ["Netflix iki kez tekrarlandı"]

    result = calculate_health_score(
        test_summary, test_categories,
        test_inflation, test_subscriptions, test_anomalies
    )

    print(f"\nFinansal Sağlık Skoru: {result['toplam_skor']}/100")
    print(f"Seviye : {result['seviye']}")
    print(f"Mesaj  : {result['mesaj']}")
    print(f"\nBileşenler:")
    for k, v in result["bilesenler"].items():
        print(f"  {k:12} : {v:3} puan — {result['detay'][k]}")