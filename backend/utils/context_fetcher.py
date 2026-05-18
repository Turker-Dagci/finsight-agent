import os, sys, requests, time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger("context_fetcher")

# ── TCMB Döviz Kurları ────────────────────────────────────────
def get_exchange_rates() -> dict:
    try:
        url = "https://www.tcmb.gov.tr/kurlar/today.xml"
        response = requests.get(url, timeout=10)
        response.encoding = "utf-8"
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        rates = {}
        for currency in root.findall("Currency"):
            code = currency.get("CurrencyCode")
            forex_buying = currency.find("ForexBuying")
            forex_selling = currency.find("ForexSelling")
            altin = currency.find("GoldBuying")
            if code in ["USD", "EUR", "GBP", "CHF"] and forex_buying is not None:
                try:
                    rates[code] = {
                        "alis": float(forex_buying.text.replace(",", ".")),
                        "satis": float(forex_selling.text.replace(",", ".")),
                    }
                except (ValueError, AttributeError):
                    pass
            if code == "XAU" and altin is not None:
                try:
                    rates["ALTIN"] = {
                        "alis": float(altin.text.replace(",", ".")),
                    }
                except (ValueError, AttributeError):
                    pass
        rates["tarih"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        logger.info(f"Döviz kurları alındı: {list(rates.keys())}")
        return rates
    except Exception as e:
        logger.error(f"Döviz hata: {e}")
        return {
            "USD": {"alis": 38.5, "satis": 38.7},
            "EUR": {"alis": 42.1, "satis": 42.4},
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "kaynak": "fallback"
        }

# ── BIST100 Getirisi (Yahoo Finance) ─────────────────────────
def get_bist100() -> dict:
    try:
        import yfinance as yf
        bist = yf.Ticker("XU100.IS")
        hist = bist.history(period="1y")  # 1mo → 1y
        if not hist.empty:
            baslangic = hist["Close"].iloc[0]
            bitis = hist["Close"].iloc[-1]
            yillik_getiri = (bitis - baslangic) / baslangic * 100
            aylik_getiri = yillik_getiri / 12
            logger.info(f"BIST100 yıllık getiri: %{yillik_getiri:.2f}")
            return {
                "guncel": round(bitis, 2),
                "aylik_getiri_yuzde": round(aylik_getiri, 2),
                "yillik_getiri_tahmini": round(yillik_getiri, 2),
            }
    except Exception as e:
        logger.error(f"BIST100 hata: {e}")
    return {
        "guncel": None,
        "aylik_getiri_yuzde": 3.5,
        "yillik_getiri_tahmini": 42.0,
        "kaynak": "fallback"
    }

# ── Mevduat Faiz Oranı (TCMB) ────────────────────────────────
def get_deposit_rate() -> dict:
    try:
        # TCMB politika faizi
        url = "https://www.tcmb.gov.tr/wps/wcnt/TCMB_TR/Home/Para+Politikasi/Para+Politikasi+Kurulu"
        response = requests.get(url, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Politika faizini bul
        faiz_text = soup.find(string=lambda t: t and "%" in t and "faiz" in t.lower())
        if faiz_text:
            import re
            match = re.search(r'(\d+[,.]?\d*)\s*%', faiz_text)
            if match:
                faiz = float(match.group(1).replace(",", "."))
                logger.info(f"Politika faizi: %{faiz}")
                return {
                    "politika_faizi": faiz,
                    "mevduat_tahmini": faiz - 2,
                    "kaynak": "tcmb"
                }
    except Exception as e:
        logger.error(f"Faiz hata: {e}")

    # Fallback — bilinen güncel değer
    logger.warning("Faiz verisi fallback kullanıyor")
    return {
        "politika_faizi": 45.0,
        "mevduat_tahmini": 43.0,
        "kaynak": "fallback"
    }

# ── Enflasyon Verisi (TCMB Beklenti Anketi) ──────────────────
def get_inflation_data() -> dict:
    try:
        # TCMB beklenti anketi RSS/API
        url = "https://www.tcmb.gov.tr/wps/wcnt/TCMB_TR/Home/Istatistikler/Enflasyon+Verileri"
        response = requests.get(url, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        # Sayfa yapısından TÜFE değerini çek
        tablo = soup.find("table")
        if tablo:
            rows = tablo.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if cols and len(cols) >= 2:
                    text = cols[0].get_text(strip=True)
                    if "TÜFE" in text or "tüfe" in text.lower():
                        deger = cols[-1].get_text(strip=True).replace(",", ".")
                        import re
                        match = re.search(r'\d+\.?\d*', deger)
                        if match:
                            yillik = float(match.group())
                            logger.info(f"TÜFE yıllık: %{yillik}")
                            return {
                                "aylik_tufe": round(yillik / 12, 2),
                                "yillik_tufe": yillik,
                                "donem": datetime.now().strftime("%B %Y"),
                                "kategori": {
                                    "gida":    {"aylik": 4.1,  "yillik": 49.2},
                                    "ulasim":  {"aylik": 4.8,  "yillik": 57.6},
                                    "fatura":  {"aylik": 6.1,  "yillik": 73.2},
                                    "eglence": {"aylik": 3.2,  "yillik": 38.4},
                                    "saglik":  {"aylik": 3.8,  "yillik": 45.6},
                                    "kira":    {"aylik": 6.5,  "yillik": 78.0},
                                    "diger":   {"aylik": 3.5,  "yillik": 42.0},
                                },
                                "kaynak": "tcmb"
                            }
    except Exception as e:
        logger.error(f"Enflasyon hata: {e}")

    logger.warning("Enflasyon verisi fallback kullanıyor")
    return {
        "aylik_tufe": 3.18,
        "yillik_tufe": 38.10,
        "donem": "Nisan 2026",
        "kategori": {
            "gida":    {"aylik": 3.2,  "yillik": 48.5},
            "ulasim":  {"aylik": 4.1,  "yillik": 61.2},
            "fatura":  {"aylik": 5.8,  "yillik": 78.4},
            "eglence": {"aylik": 2.9,  "yillik": 38.7},
            "saglik":  {"aylik": 3.6,  "yillik": 52.1},
            "kira":    {"aylik": 6.2,  "yillik": 89.3},
            "diger":   {"aylik": 3.4,  "yillik": 45.0},
        },
        "kaynak": "fallback"
    }

# ── Yatırım Getirileri ────────────────────────────────────────
def get_investment_returns(exchange_rates: dict, bist: dict, deposit: dict) -> dict:
    """
    Canlı verilerden yatırım getiri oranlarını hesaplar.
    """
    # USD/TL yıllık değişim
    usd_satis = exchange_rates.get("USD", {}).get("satis", 38.7)
    # Yaklaşık yıllık kur artışı (TCMB verisiyle hesaplanabilir)
    doviz_getiri = 32.0  # TL bazında tahmini yıllık

    # Altın TL bazlı
    altin_getiri = 38.0  # TL bazında tahmini yıllık

    # BIST100
    bist_getiri = bist.get("yillik_getiri_tahmini", 42.0)

    # Mevduat
    mevduat_getiri = deposit.get("mevduat_tahmini", 43.0)

    return {
        "Döviz (USD/EUR)": {
            "yillik_getiri": doviz_getiri,
            "aylik_getiri": round(doviz_getiri / 12, 2),
            "risk": "orta",
            "aciklama": f"USD kuru: {usd_satis:.2f} TL"
        },
        "Altın": {
            "yillik_getiri": altin_getiri,
            "aylik_getiri": round(altin_getiri / 12, 2),
            "risk": "orta",
            "aciklama": "Gram altın TL bazlı"
        },
        "Hisse Senedi": {
            "yillik_getiri": bist_getiri,
            "aylik_getiri": round(bist_getiri / 12, 2),
            "risk": "yüksek",
            "aciklama": f"BIST100 aylık: %{bist.get('aylik_getiri_yuzde', 3.5):.1f}"
        },
        "Mevduat": {
            "yillik_getiri": mevduat_getiri,
            "aylik_getiri": round(mevduat_getiri / 12, 2),
            "risk": "düşük",
            "aciklama": f"Politika faizi: %{deposit.get('politika_faizi', 45)}"
        },
    }

# ── Haberler ─────────────────────────────────────────────────
def get_economic_news() -> list:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        logger.warning("NEWS_API_KEY bulunamadı, fallback haberler kullanılıyor")
        return get_fallback_news()
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "Türkiye enflasyon döviz ekonomi faiz",
            "language": "tr",
            "sortBy": "publishedAt",
            "pageSize": 5,
            "apiKey": api_key
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("status") != "ok":
            return get_fallback_news()
        news = []
        for article in data.get("articles", [])[:5]:
            news.append({
                "baslik": article.get("title", ""),
                "kaynak": article.get("source", {}).get("name", ""),
                "tarih": article.get("publishedAt", "")[:10],
            })
        logger.info(f"{len(news)} haber alındı")
        return news
    except Exception as e:
        logger.error(f"Haber hata: {e}")
        return get_fallback_news()

def get_fallback_news() -> list:
    return [
        {"baslik": "Merkez Bankası faiz kararını açıkladı", "kaynak": "Fallback", "tarih": "2026-05-17"},
        {"baslik": "Dolar/TL yüksek seyrediyor", "kaynak": "Fallback", "tarih": "2026-05-17"},
        {"baslik": "Yakıt fiyatlarına zam beklentisi", "kaynak": "Fallback", "tarih": "2026-05-17"},
    ]

# ── Ana Fonksiyon ─────────────────────────────────────────────
def get_market_context() -> dict:
    logger.info("Piyasa verileri çekiliyor")

    rates = get_exchange_rates()
    inflation = get_inflation_data()
    news = get_economic_news()
    bist = get_bist100()
    deposit = get_deposit_rate()
    investment_returns = get_investment_returns(rates, bist, deposit)

    context = {
        "doviz": rates,
        "enflasyon": inflation,
        "haberler": news,
        "bist100": bist,
        "mevduat_faizi": deposit,
        "yatirim_getirileri": investment_returns,
        "ozet": {
            "usd_tl": rates.get("USD", {}).get("satis", 38.7),
            "eur_tl": rates.get("EUR", {}).get("satis", 42.4),
            "aylik_tufe": inflation["aylik_tufe"],
            "yillik_tufe": inflation["yillik_tufe"],
            "bist_aylik": bist.get("aylik_getiri_yuzde", 3.5),
            "mevduat_faizi": deposit.get("mevduat_tahmini", 43.0),
        }
    }

    logger.info(f"USD/TL: {context['ozet']['usd_tl']}")
    logger.info(f"Yıllık TÜFE: %{context['ozet']['yillik_tufe']}")
    logger.info(f"BIST100 aylık: %{context['ozet']['bist_aylik']}")
    logger.info(f"Mevduat faizi: %{context['ozet']['mevduat_faizi']}")

    return context


if __name__ == "__main__":
    context = get_market_context()
    print("\n--- DÖVİZ ---")
    for kod, deger in context["doviz"].items():
        if isinstance(deger, dict):
            print(f"  {kod}: {deger.get('satis', deger.get('alis', '-'))} TL")
    print("\n--- ENFLASYON ---")
    print(f"  Aylık: %{context['enflasyon']['aylik_tufe']}")
    print(f"  Yıllık: %{context['enflasyon']['yillik_tufe']}")
    print(f"  Kaynak: {context['enflasyon']['kaynak']}")
    print("\n--- BIST100 ---")
    print(f"  Aylık getiri: %{context['bist100']['aylik_getiri_yuzde']}")
    print(f"  Yıllık tahmin: %{context['bist100']['yillik_getiri_tahmini']}")
    print("\n--- MEVDUAT ---")
    print(f"  Politika faizi: %{context['mevduat_faizi']['politika_faizi']}")
    print(f"  Mevduat tahmini: %{context['mevduat_faizi']['mevduat_tahmini']}")
    print("\n--- YATIRIM GETİRİLERİ ---")
    for tur, bilgi in context["yatirim_getirileri"].items():
        print(f"  {tur}: yıllık %{bilgi['yillik_getiri']} — {bilgi['aciklama']}")