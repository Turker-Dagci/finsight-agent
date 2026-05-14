import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from agents.analyst_agent import (
    categorize_transactions,
    calculate_inflation_impact,
    calculate_tax_breakdown,
    detect_anomalies,
    detect_subscriptions
)

# ── Test verisi ───────────────────────────────────────────────
SAMPLE_TRANSACTIONS = [
    {"tarih": "2026-04-01", "aciklama": "Maaş", "tutar": 42000.0, "tur": "gelir", "kategori": "maas"},
    {"tarih": "2026-04-02", "aciklama": "Migros Market", "tutar": -1240.5, "tur": "gider", "kategori": "gida"},
    {"tarih": "2026-04-03", "aciklama": "Shell Yakıt", "tutar": -1850.0, "tur": "gider", "kategori": "ulasim"},
    {"tarih": "2026-04-04", "aciklama": "Netflix Abonelik", "tutar": -349.99, "tur": "gider", "kategori": "eglence"},
    {"tarih": "2026-04-08", "aciklama": "BEDAŞ Elektrik", "tutar": -2340.0, "tur": "gider", "kategori": "fatura"},
    {"tarih": "2026-04-20", "aciklama": "Netflix Abonelik", "tutar": -349.99, "tur": "gider", "kategori": "eglence"},
    {"tarih": "2026-04-25", "aciklama": "Kira Ödemesi", "tutar": -12000.0, "tur": "gider", "kategori": "kira"},
]

# ── Testler ───────────────────────────────────────────────────
def test_kategorilendirme_geliri_dahil_etmez():
    result = categorize_transactions(SAMPLE_TRANSACTIONS)
    assert "maas" not in result, "Gelir kategorilere dahil edilmemeli"

def test_kategorilendirme_toplam_dogru():
    result = categorize_transactions(SAMPLE_TRANSACTIONS)
    assert result["gida"] == 1240.5
    assert result["ulasim"] == 1850.0
    assert result["kira"] == 12000.0

def test_enflasyon_reel_deger_dusuk():
    categories = {"gida": 1000.0, "ulasim": 1000.0}
    result = calculate_inflation_impact(categories)
    for kategori, deger in result.items():
        assert deger["reel"] < deger["nominal"], \
            f"{kategori} için reel değer nominalden küçük olmalı"

def test_enflasyon_kayip_pozitif():
    categories = {"kira": 12000.0}
    result = calculate_inflation_impact(categories)
    assert result["kira"]["kayip"] > 0, "Kayıp pozitif olmalı"

def test_vergi_ulasim_otv_iceriyor():
    categories = {"ulasim": 1000.0}
    result = calculate_tax_breakdown(categories)
    assert result["ulasim"]["otv"] > 0, "Ulaşımda ÖTV olmalı"

def test_vergi_kira_sifir():
    categories = {"kira": 10000.0}
    result = calculate_tax_breakdown(categories)
    assert result["kira"]["kdv"] == 0, "Kirada KDV olmamalı"
    assert result["kira"]["otv"] == 0, "Kirada ÖTV olmamalı"

def test_vergi_toplam_pozitif():
    categories = {"gida": 5000.0, "ulasim": 3000.0}
    result = calculate_tax_breakdown(categories)
    assert result["TOPLAM"]["toplam_vergi"] > 0

def test_anomali_mujekrer_odeme():
    result = detect_anomalies(SAMPLE_TRANSACTIONS)
    assert len(result) > 0, "Netflix tekrarı anomali olarak tespit edilmeli"
    assert any("netflix" in a.lower() for a in result)

def test_anomali_gelir_kontrol_edilmez():
    sadece_gelir = [
        {"aciklama": "Maaş", "tutar": 42000.0, "tur": "gelir", "kategori": "maas"},
        {"aciklama": "Maaş", "tutar": 42000.0, "tur": "gelir", "kategori": "maas"},
    ]
    result = detect_anomalies(sadece_gelir)
    assert len(result) == 0, "Gelir işlemleri anomali sayılmamalı"

def test_abonelik_tespiti():
    result = detect_subscriptions(SAMPLE_TRANSACTIONS)
    assert len(result) > 0, "Netflix abonelik olarak tespit edilmeli"
    aciklamalar = [s["aciklama"].lower() for s in result]
    assert any("netflix" in a for a in aciklamalar)

def test_abonelik_tutar_pozitif():
    result = detect_subscriptions(SAMPLE_TRANSACTIONS)
    for s in result:
        assert s["tutar"] > 0, "Abonelik tutarı pozitif olmalı"

# ── Çalıştır ──────────────────────────────────────────────────
if __name__ == "__main__":
    testler = [
        test_kategorilendirme_geliri_dahil_etmez,
        test_kategorilendirme_toplam_dogru,
        test_enflasyon_reel_deger_dusuk,
        test_enflasyon_kayip_pozitif,
        test_vergi_ulasim_otv_iceriyor,
        test_vergi_kira_sifir,
        test_vergi_toplam_pozitif,
        test_anomali_mujekrer_odeme,
        test_anomali_gelir_kontrol_edilmez,
        test_abonelik_tespiti,
        test_abonelik_tutar_pozitif,
    ]

    basarili = 0
    basarisiz = 0

    print("=" * 50)
    print("FinSight — Analyst Agent Testleri")
    print("=" * 50)

    for test in testler:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            basarili += 1
        except AssertionError as e:
            print(f"  FAIL  {test.__name__}: {e}")
            basarisiz += 1
        except Exception as e:
            print(f"  ERROR {test.__name__}: {e}")
            basarisiz += 1

    print("=" * 50)
    print(f"Sonuç: {basarili} başarılı, {basarisiz} başarısız")
    print("=" * 50)