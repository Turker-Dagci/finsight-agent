import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
logger = setup_logger("advisory_agent")

from utils.gemini import generate_with_retry
from dotenv import load_dotenv
from utils.context_fetcher import get_market_context

load_dotenv()

def calculate_fx_shield(parsed_summary: dict, exchange_rates: dict) -> dict:
    """Döviz kalkanı analizi — aylık harcamanın döviz karşılığı."""
    toplam_gider = abs(parsed_summary.get("toplam_gider", 0) or 0)
    usd_rate = exchange_rates.get("USD", {}).get("satis", 38.7)
    eur_rate = exchange_rates.get("EUR", {}).get("satis", 42.4)

    return {
        "aylik_gider_tl": toplam_gider,
        "aylik_gider_usd": round(toplam_gider / usd_rate, 2),
        "aylik_gider_eur": round(toplam_gider / eur_rate, 2),
        "usd_kur": usd_rate,
        "eur_kur": eur_rate,
        "yorum": (
            f"Aylık {toplam_gider:,.0f} TL harcamanız, "
            f"güncel kurla yaklaşık {toplam_gider/usd_rate:,.0f} USD veya "
            f"{toplam_gider/eur_rate:,.0f} EUR'ya karşılık geliyor."
        )
    }

def generate_proactive_alerts(
    categories: dict,
    inflation_analysis: dict,
    parsed_summary: dict,
    subscriptions: list
) -> list:
    """Kullanıcı sormadan proaktif uyarılar üretir."""
    alerts = []

    toplam_gelir = parsed_summary.get("toplam_gelir", 0)
    toplam_gider = parsed_summary.get("toplam_gider", 0)

    # Tasarruf oranı uyarısı
    if toplam_gelir > 0:
        tasarruf = (toplam_gelir - toplam_gider) / toplam_gelir * 100
        if tasarruf < 10:
            alerts.append(f"⚠ Tasarruf oranınız %{tasarruf:.1f} — finansal güvenlik için en az %20 önerilir.")
        elif tasarruf < 20:
            alerts.append(f"📊 Tasarruf oranınız %{tasarruf:.1f} — biraz daha kısabilirsiniz.")

    # Yüksek enflasyonlu kategori uyarısı
    for kategori, inf in inflation_analysis.items():
        if inf.get("yillik_enflasyon", 0) > 60 and inf.get("nominal", 0) > 1000:
            alerts.append(
                f"🔥 {kategori.upper()} kategorisinde yıllık enflasyon %{inf['yillik_enflasyon']} — "
                f"bu kategoride {inf['kayip']:.0f} TL satın alma gücü kaybettiniz."
            )

    # Abonelik uyarısı
    if len(subscriptions) >= 3:
        toplam_abone = sum(s["tutar"] for s in subscriptions)
        alerts.append(
            f"📱 {len(subscriptions)} aktif aboneliğiniz var, toplam aylık {toplam_abone:.0f} TL. "
            f"İhtiyaç duymadıklarınızı iptal etmeyi düşünün."
        )

    # Kira yükü uyarısı
    kira = categories.get("kira", 0)
    if toplam_gelir > 0 and kira / toplam_gelir > 0.35:
        alerts.append(
            f"🏠 Kira gelirinizin %{kira/toplam_gelir*100:.0f}'ini alıyor — "
            f"ideal oran %30'un altı olmalı."
        )

    return alerts

def generate_advisory_response(
    user_query: str,
    categories: dict,
    inflation_analysis: dict,
    tax_breakdown: dict,
    anomalies: list,
    subscriptions: list,
    parsed_summary: dict,
    fx_shield: dict,
    market_context: dict,
    proactive_alerts: list,
    financial_profile: dict = None
) -> str:
    """Gemini ile kapsamlı finansal tavsiye üretir."""

    doviz_ozet = f"USD/TL: {market_context['ozet']['usd_tl']}, EUR/TL: {market_context['ozet']['eur_tl']}"
    enflasyon_ozet = f"Aylık TÜFE: %{market_context['ozet']['aylik_tufe']}, Yıllık: %{market_context['ozet']['yillik_tufe']}"
    haberler = "\n".join([f"- {h['baslik']}" for h in market_context.get("haberler", [])])
    kategori_metin = "\n".join([f"- {k}: {v:,.0f} TL" for k, v in categories.items()])
    vergi_toplam = tax_breakdown.get("TOPLAM", {}).get("toplam_vergi", 0)
    enflasyon_metin = "\n".join([
        f"- {k}: nominal {v['nominal']:,.0f} TL, reel {v['reel']:,.0f} TL, kayıp {v['kayip']:,.0f} TL"
        for k, v in inflation_analysis.items()
    ])
    anomali_metin = "\n".join(anomalies) if anomalies else "Anomali tespit edilmedi."
    abone_metin = "\n".join([
        f"- {s['aciklama']}: {s['tutar']:.0f} TL"
        for s in subscriptions
    ]) if subscriptions else "Abonelik tespit edilmedi."

    profil_metin = ""
    if financial_profile:
        profil_metin = f"""
FİNANSAL PROFİL:
- Gelir kaynağı: {financial_profile.get('gelir_kaynak', 'Belirtilmedi')}
- Ek gelir: {financial_profile.get('ek_gelir', 'Yok')}
- Toplam borç: {financial_profile.get('borclar', 'Belirtilmedi')}
- Yatırımlar: {financial_profile.get('yatirimlar', 'Belirtilmedi')}
"""

    KISMA_KURALLARI = """
KESİNLİKLE ÖNERMEMEN GEREKEN KISINTLAR:
- Kira: Sözleşme bağlayıcıdır, kesilemez
- Temel gıda (market alışverişi): Sağlık için zorunludur
- Elektrik, su, doğalgaz faturaları: Zorunlu giderdir
- Sağlık harcamaları: Kesilemez
- Ulaşım (işe gidiş): Zorunludur
- Kredi/borç ödemeleri: Yasal yükümlülüktür

ÖNERİLEBİLECEK KISINTLAR (önce bunlara bak):
- Kullanılmayan veya az kullanılan abonelikler
- Kafe, restoran, dışarıda yeme/içme
- Eğlence (sinema, bowling, alışveriş)
- Anlık ve plansız alışverişler
- ATM nakit çekimleri

NAKİT İHTİYACI İÇİN:
1. Bu ihtiyaç zorunlu mu, ertelenebilir mi?
2. Mevcut tasarruftan karşılanabilir mi?
3. Sadece kısılabilir harcamalardan tasarruf öner.
Asla zorunlu giderleri kısmayı önerme.

BİRİKİM HEDEFİ İÇİN:
Hedefe ulaşmak için gereken ek tasarrufu hesapla.
Bu tasarrufu YALNIZCA kısılabilir harcamalardan karşıla.
"""

    prompt = f"""{KISMA_KURALLARI}

Sen FinSight, Türkiye'deki KOBİ ve bireyler için çalışan uzman bir finansal analiz asistanısın.
Kullanıcının banka ekstresini analiz ettin ve aşağıdaki verilere sahipsin.
Türkçe, samimi, anlaşılır ve somut tavsiyeler ver. Genel laflar etme.

KULLANICI SORUSU: {user_query}

HARCAMA KATEGORİLERİ:
{kategori_metin}

ÖZET:
- Toplam Gelir: {parsed_summary.get('toplam_gelir', 0):,.0f} TL
- Toplam Gider: {parsed_summary.get('toplam_gider', 0):,.0f} TL
- Net: {parsed_summary.get('toplam_gelir', 0) - parsed_summary.get('toplam_gider', 0):,.0f} TL

ENFLASYON DÜZELTMELİ ANALİZ:
{enflasyon_metin}

GİZLİ VERGİ YÜKÜ:
- Bu dönem harcamalarında toplam {vergi_toplam:,.0f} TL vergi ödendi (KDV + ÖTV dahil)

ABONELİKLER:
{abone_metin}

ANOMALİLER:
{anomali_metin}

DÖVİZ KALKANI:
{fx_shield.get('yorum', '')}

GÜNCEL PİYASA BAĞLAMI:
- {doviz_ozet}
- {enflasyon_ozet}
Son haberler:
{haberler}
{profil_metin}

PROAKTİF UYARILAR:
{chr(10).join(proactive_alerts) if proactive_alerts else 'Kritik uyarı yok.'}

Lütfen şunları içeren bir yanıt ver:
1. Kullanıcının sorusuna doğrudan cevap
2. En önemli 2-3 bulgu (kısa, net)
3. Güncel piyasa bağlamı ışığında somut tavsiye
4. Önümüzdeki ay için 1 eylem önerisi

Yanıtı maksimum 300 kelime tut. Madde madde yaz."""

    return generate_with_retry(prompt, use_system_prompt=True)

def run_advisory(
    user_query: str,
    categories: dict,
    inflation_analysis: dict,
    tax_breakdown: dict,
    anomalies: list,
    subscriptions: list,
    parsed_summary: dict,
    financial_profile: dict = None
) -> dict:
    """Advisory Agent ana fonksiyonu."""
    logger.info("Piyasa bağlamı çekiliyor")
    market_context = get_market_context()

    logger.info("Döviz kalkanı hesaplanıyor")
    fx_shield = calculate_fx_shield(parsed_summary, market_context["doviz"])

    logger.info("Proaktif uyarılar üretiliyor")
    alerts = generate_proactive_alerts(
        categories, inflation_analysis, parsed_summary, subscriptions
    )

    logger.info("Gemini yanıtı üretiliyor")
    response = generate_advisory_response(
        user_query=user_query,
        categories=categories,
        inflation_analysis=inflation_analysis,
        tax_breakdown=tax_breakdown,
        anomalies=anomalies,
        subscriptions=subscriptions,
        parsed_summary=parsed_summary,
        fx_shield=fx_shield,
        market_context=market_context,
        proactive_alerts=alerts,
        financial_profile=financial_profile
    )

    return {
        "fx_shield": fx_shield,
        "proactive_alerts": alerts,
        "market_context": market_context,
        "final_response": response
    }


if __name__ == "__main__":
    # Demo test
    test_categories = {
        "gida": 5411.5, "ulasim": 6450.0,
        "eglence": 1379.97, "fatura": 3840.0,
        "kira": 12000.0, "saglik": 450.0, "diger": 2720.0
    }
    test_inflation = {
        "gida":    {"nominal": 5411.5, "reel": 5243.8, "kayip": 167.7, "aylik_enflasyon": 3.2, "yillik_enflasyon": 48.5},
        "ulasim":  {"nominal": 6450.0, "reel": 6194.1, "kayip": 255.9, "aylik_enflasyon": 4.1, "yillik_enflasyon": 61.2},
        "kira":    {"nominal": 12000.0, "reel": 11299.4, "kayip": 700.6, "aylik_enflasyon": 6.2, "yillik_enflasyon": 89.3},
    }
    test_tax = {"TOPLAM": {"toplam_vergi": 4230.5}}
    test_summary = {"toplam_gelir": 42000.0, "toplam_gider": 35994.46}
    test_subscriptions = [
        {"aciklama": "Netflix", "tutar": 349.99, "tarih": "2026-04-04"},
        {"aciklama": "Spotify", "tutar": 99.99, "tarih": "2026-04-05"},
    ]

    result = run_advisory(
        user_query="Bu ay nasıl harcadım, önümüzdeki ay ne yapmalıyım?",
        categories=test_categories,
        inflation_analysis=test_inflation,
        tax_breakdown=test_tax,
        anomalies=["Netflix bu dönem 2 kez tekrarlandı."],
        subscriptions=test_subscriptions,
        parsed_summary=test_summary
    )

    print("\n--- PROAKTİF UYARILAR ---")
    for a in result["proactive_alerts"]:
        print(f"  {a}")

    print("\n--- DÖVİZ KALKANI ---")
    print(f"  {result['fx_shield']['yorum']}")

    print("\n--- GEMİNİ TAVSİYESİ ---")
    print(result["final_response"])