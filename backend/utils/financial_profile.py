import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger

logger = setup_logger("financial_profile")

def calculate_budget_plan(
    profile: dict,
    categories: dict,
    parsed_summary: dict,
    hedefler: list = None
) -> dict:
    """
    Kullanıcı profiline ve hedeflerine göre
    kişiselleştirilmiş bütçe planı üretir.
    """
    aylik_gelir = profile.get("aylik_gelir", 0)
    toplam_gider = parsed_summary.get("toplam_gider", 0)
    mevcut_tasarruf = max(aylik_gelir - toplam_gider, 0)

    if aylik_gelir == 0:
        aylik_gelir = parsed_summary.get("toplam_gelir", 0)
        mevcut_tasarruf = max(aylik_gelir - toplam_gider, 0)

    # 50/30/20 kuralı bazlı ideal bütçe
    ideal_zorunlu = aylik_gelir * 0.50
    ideal_istekler = aylik_gelir * 0.30
    ideal_tasarruf = aylik_gelir * 0.20

    # Mevcut durum
    zorunlu_kategoriler = ["kira", "fatura", "saglik", "ulasim"]
    istek_kategoriler = ["eglence", "diger"]

    mevcut_zorunlu = sum(
        categories.get(k, 0) for k in zorunlu_kategoriler
    )
    mevcut_istekler = sum(
        categories.get(k, 0) for k in istek_kategoriler
    )
    mevcut_gida = categories.get("gida", 0)

    # Hedef analizi
    hedef_analizi = []
    if hedefler:
        for hedef in hedefler:
            ad = hedef.get("ad", "Hedef")
            hedef_tutar = hedef.get("hedef_tutar", 0)
            aylik_butce = hedef.get("aylik_butce", 0)
            sure_ay = hedef.get("sure_ay", 12)

            if hedef_tutar > 0 and mevcut_tasarruf > 0:
                gercekci_sure = round(hedef_tutar / mevcut_tasarruf)
                fark = gercekci_sure - sure_ay
            else:
                gercekci_sure = None
                fark = None

            if aylik_butce > 0:
                kismalar = []
                kalan = aylik_butce - mevcut_tasarruf
                if kalan > 0:
                    if mevcut_istekler > 0:
                        eglence_kesinti = min(
                            kalan * 0.4,
                            mevcut_istekler * 0.3
                        )
                        kismalar.append({
                            "kategori": "Eğlence & Diğer",
                            "kesinti": round(eglence_kesinti, 0),
                            "aciklama": "Eğlence harcamalarından %30 kısma"
                        })
                        kalan -= eglence_kesinti

                    if kalan > 0 and mevcut_gida > 0:
                        gida_kesinti = min(
                            kalan,
                            mevcut_gida * 0.15
                        )
                        kismalar.append({
                            "kategori": "Gıda",
                            "kesinti": round(gida_kesinti, 0),
                            "aciklama": "Market alışverişinde %15 verimlilik"
                        })

                hedef_analizi.append({
                    "ad": ad,
                    "hedef_tutar": hedef_tutar,
                    "aylik_butce": aylik_butce,
                    "sure_ay": sure_ay,
                    "mevcut_tasarruf": round(mevcut_tasarruf, 0),
                    "gercekci_sure_ay": gercekci_sure,
                    "sure_farki": fark,
                    "kismalar": kismalar,
                })

    logger.info(f"Bütçe planı hazırlandı: {len(hedef_analizi)} hedef")

    return {
        "aylik_gelir": aylik_gelir,
        "toplam_gider": toplam_gider,
        "mevcut_tasarruf": round(mevcut_tasarruf, 0),
        "ideal_dagilim": {
            "zorunlu_50": round(ideal_zorunlu, 0),
            "istekler_30": round(ideal_istekler, 0),
            "tasarruf_20": round(ideal_tasarruf, 0),
        },
        "mevcut_dagilim": {
            "zorunlu": round(mevcut_zorunlu, 0),
            "istekler": round(mevcut_istekler, 0),
            "gida": round(mevcut_gida, 0),
            "tasarruf": round(mevcut_tasarruf, 0),
        },
        "hedef_analizi": hedef_analizi,
        "genel_durum": (
            "sağlıklı" if mevcut_tasarruf >= ideal_tasarruf
            else "geliştirilmeli"
        )
    }


def build_profile_context(profile: dict, budget_plan: dict) -> str:
    """
    Advisory Agent'a verilecek profil bağlamı metni.
    """
    hedef_metni = ""
    for h in budget_plan.get("hedef_analizi", []):
        hedef_metni += f"\n- Hedef: {h['ad']}"
        if h.get("hedef_tutar"):
            hedef_metni += f" ({h['hedef_tutar']:,.0f} TL)"
        if h.get("gercekci_sure_ay"):
            hedef_metni += f" — mevcut hızla {h['gercekci_sure_ay']} ayda ulaşılır"
        if h.get("kismalar"):
            for k in h["kismalar"]:
                hedef_metni += (
                    f"\n  → {k['kategori']}'den "
                    f"{k['kesinti']:,.0f} TL kısılabilir"
                )

    return f"""
FİNANSAL PROFİL:
- Gelir kaynağı: {profile.get('gelir_kaynak', 'Belirtilmedi')}
- Aylık net gelir: {profile.get('aylik_gelir', 0):,.0f} TL
- Ek gelir: {profile.get('ek_gelir', 'Yok')}
- Toplam borç: {profile.get('borclar', 'Belirtilmedi')}
- Yatırımlar: {profile.get('yatirimlar', 'Belirtilmedi')}

BÜTÇE DURUMU (50/30/20 Kuralı):
- İdeal tasarruf: {budget_plan['ideal_dagilim']['tasarruf_20']:,.0f} TL/ay
- Mevcut tasarruf: {budget_plan['mevcut_tasarruf']:,.0f} TL/ay
- Genel durum: {budget_plan['genel_durum']}

FİNANSAL HEDEFLER:{hedef_metni if hedef_metni else ' Belirtilmedi'}
"""


if __name__ == "__main__":
    test_profile = {
        "gelir_kaynak": "Maaş",
        "aylik_gelir": 42000,
        "ek_gelir": "Yok",
        "borclar": "50.000 TL kredi",
        "yatirimlar": "Döviz",
    }
    test_categories = {
        "gida": 5411.5,
        "ulasim": 6450.0,
        "eglence": 1379.97,
        "fatura": 3840.0,
        "kira": 12000.0,
    }
    test_summary = {
        "toplam_gelir": 42000.0,
        "toplam_gider": 35994.46
    }
    test_hedefler = [
        {
            "ad": "Yurt Dışı Tatil",
            "hedef_tutar": 30000,
            "aylik_butce": 3000,
            "sure_ay": 10
        },
        {
            "ad": "Acil Durum Fonu",
            "hedef_tutar": 50000,
            "aylik_butce": 5000,
            "sure_ay": 12
        }
    ]

    plan = calculate_budget_plan(
        test_profile, test_categories,
        test_summary, test_hedefler
    )

    print(f"Aylık Gelir    : {plan['aylik_gelir']:,.0f} TL")
    print(f"Mevcut Tasarruf: {plan['mevcut_tasarruf']:,.0f} TL")
    print(f"Genel Durum    : {plan['genel_durum']}")
    print(f"\n50/30/20 İdeal Dağılım:")
    for k, v in plan["ideal_dagilim"].items():
        print(f"  {k:20}: {v:,.0f} TL")
    print(f"\nHedef Analizi:")
    for h in plan["hedef_analizi"]:
        print(f"\n  [{h['ad']}]")
        print(f"  Hedef tutar    : {h['hedef_tutar']:,.0f} TL")
        print(f"  Mevcut hızla   : {h['gercekci_sure_ay']} ay")
        print(f"  Hedef süre     : {h['sure_ay']} ay")
        if h.get("kismalar"):
            print(f"  Kısma önerileri:")
            for k in h["kismalar"]:
                print(f"    → {k['kategori']}: {k['kesinti']:,.0f} TL")

    print(f"\nProfil Bağlamı:")
    print(build_profile_context(test_profile, plan))