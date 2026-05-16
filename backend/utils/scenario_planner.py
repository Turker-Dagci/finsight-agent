import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger

logger = setup_logger("scenario_planner")

def simulate_scenario(
    senaryo_tutar: float,
    senaryo_aciklama: str,
    parsed_summary: dict,
    hedef_tutar: float = None,
    sure_ay: int = 12
) -> dict:
    """
    "Ya şöyle olursa?" simülasyonu.
    Tek seferlik veya aylık harcama senaryosu simüle eder.
    """
    aylik_gelir = parsed_summary.get("toplam_gelir", 0)
    aylik_gider = parsed_summary.get("toplam_gider", 0)
    mevcut_tasarruf = max(aylik_gelir - aylik_gider, 0)

    # Yıllık projeksiyon — mevcut hız
    yillik_tasarruf_mevcut = mevcut_tasarruf * 12

    # Senaryo sonrası
    senaryo_tasarruf = max(mevcut_tasarruf - senaryo_tutar, 0)
    yillik_tasarruf_senaryo = senaryo_tasarruf * 12

    # Enflasyon etkisi (%38 yıllık)
    enflasyon_orani = 0.38
    reel_mevcut = yillik_tasarruf_mevcut / (1 + enflasyon_orani)
    reel_senaryo = yillik_tasarruf_senaryo / (1 + enflasyon_orani)

    # Hedef analizi
    hedef_analizi = None
    if hedef_tutar and hedef_tutar > 0:
        if mevcut_tasarruf > 0:
            mevcut_sure = round(hedef_tutar / mevcut_tasarruf)
        else:
            mevcut_sure = None

        if senaryo_tasarruf > 0:
            senaryo_sure = round(hedef_tutar / senaryo_tasarruf)
        else:
            senaryo_sure = None

        hedef_analizi = {
            "hedef_tutar": hedef_tutar,
            "mevcut_sure_ay": mevcut_sure,
            "senaryo_sure_ay": senaryo_sure,
            "gecikme_ay": (
                senaryo_sure - mevcut_sure
                if mevcut_sure and senaryo_sure
                else None
            )
        }

    # Tavsiye üret
    etki_orani = senaryo_tutar / mevcut_tasarruf if mevcut_tasarruf > 0 else 1

    if etki_orani == 0:
        etki_seviyesi = "minimal"
        tavsiye = "Bu harcama mevcut tasarruf hedefinizi etkilemez."
    elif etki_orani < 0.2:
        etki_seviyesi = "düşük"
        tavsiye = f"Bu harcama tasarrufunuzun %{etki_orani*100:.0f}'ini etkiler — yönetilebilir."
    elif etki_orani < 0.5:
        etki_seviyesi = "orta"
        tavsiye = (
            f"Bu harcama aylık tasarrufunuzu "
            f"{mevcut_tasarruf:,.0f} TL'den "
            f"{senaryo_tasarruf:,.0f} TL'ye düşürür."
        )
    elif etki_orani < 1:
        etki_seviyesi = "yüksek"
        tavsiye = (
            f"Dikkat: Bu harcama tasarrufunuzun "
            f"%{etki_orani*100:.0f}'ini tüketir. "
            f"Harcamayı 2-3 aya yaymayı düşünebilirsiniz."
        )
    else:
        etki_seviyesi = "kritik"
        tavsiye = (
            "Bu harcama mevcut tasarrufu aşıyor. "
            "Başka kategorilerden kısma yapılması gerekir."
        )

    logger.info(
        f"Senaryo simüle edildi: '{senaryo_aciklama}' "
        f"— {senaryo_tutar:,.0f} TL — etki: {etki_seviyesi}"
    )

    return {
        "senaryo": {
            "aciklama": senaryo_aciklama,
            "tutar": senaryo_tutar,
        },
        "mevcut_durum": {
            "aylik_tasarruf": round(mevcut_tasarruf, 0),
            "yillik_tasarruf": round(yillik_tasarruf_mevcut, 0),
            "reel_yillik": round(reel_mevcut, 0),
        },
        "senaryo_sonrasi": {
            "aylik_tasarruf": round(senaryo_tasarruf, 0),
            "yillik_tasarruf": round(yillik_tasarruf_senaryo, 0),
            "reel_yillik": round(reel_senaryo, 0),
            "fark": round(yillik_tasarruf_mevcut - yillik_tasarruf_senaryo, 0),
        },
        "etki_seviyesi": etki_seviyesi,
        "tavsiye": tavsiye,
        "hedef_analizi": hedef_analizi,
    }


if __name__ == "__main__":
    test_summary = {
        "toplam_gelir": 42000.0,
        "toplam_gider": 35994.46
    }

    senaryolar = [
        {
            "aciklama": "Yurt dışı tatil",
            "tutar": 15000,
            "hedef_tutar": 50000,
            "sure_ay": 12
        },
        {
            "aciklama": "Yeni telefon",
            "tutar": 25000,
            "hedef_tutar": 50000,
            "sure_ay": 12
        },
        {
            "aciklama": "Aylık spor salonu + takviye",
            "tutar": 2000,
            "hedef_tutar": None,
            "sure_ay": 12
        },
    ]

    print("Senaryo Planlama Testi")
    print("=" * 60)

    for s in senaryolar:
        result = simulate_scenario(
            senaryo_tutar=s["tutar"],
            senaryo_aciklama=s["aciklama"],
            parsed_summary=test_summary,
            hedef_tutar=s.get("hedef_tutar"),
            sure_ay=s.get("sure_ay", 12)
        )

        print(f"\nSenaryo  : {result['senaryo']['aciklama']}")
        print(f"Tutar    : {result['senaryo']['tutar']:,.0f} TL")
        print(f"Etki     : {result['etki_seviyesi'].upper()}")
        print(f"Tavsiye  : {result['tavsiye']}")
        print(f"Mevcut yıllık tasarruf : {result['mevcut_durum']['yillik_tasarruf']:,.0f} TL")
        print(f"Senaryo yıllık tasarruf: {result['senaryo_sonrasi']['yillik_tasarruf']:,.0f} TL")
        print(f"Fark     : {result['senaryo_sonrasi']['fark']:,.0f} TL")

        if result.get("hedef_analizi"):
            h = result["hedef_analizi"]
            print(f"Hedef ({h['hedef_tutar']:,.0f} TL):")
            print(f"  Mevcut hızla  : {h['mevcut_sure_ay']} ay")
            print(f"  Senaryo sonrası: {h['senaryo_sure_ay']} ay")
            if h.get("gecikme_ay"):
                print(f"  Gecikme       : {h['gecikme_ay']} ay")
        print("-" * 40)