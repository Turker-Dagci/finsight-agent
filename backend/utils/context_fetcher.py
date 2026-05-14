import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
logger = setup_logger("context_fetcher")
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── TCMB Döviz Kurları ────────────────────────────────────────
def get_exchange_rates() -> dict:
    """TCMB'den güncel döviz kurlarını çeker."""
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

            if code in ["USD", "EUR", "GBP", "CHF"] and forex_buying is not None:
                try:
                    rates[code] = {
                        "alis": float(forex_buying.text.replace(",", ".")),
                        "satis": float(forex_selling.text.replace(",", ".")),
                    }
                except (ValueError, AttributeError):
                    pass

        # Altın (gram)
        altin_url = "https://api.collectapi.com/economy/goldPrice"
        try:
            altin_response = requests.get(
                altin_url,
                headers={"authorization": "apikey free"},
                timeout=5
            )
            if altin_response.status_code == 200:
                data = altin_response.json()
                for item in data.get("result", []):
                    if item.get("name") == "Gram Altın":
                        rates["ALTIN"] = {"alis": float(item.get("buying", 0))}
        except Exception:
            pass  # Altın opsiyonel

        rates["tarih"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        logger.info(f"Döviz kurları alındı: {list(rates.keys())}")
        return rates

    except Exception as e:
        logger.error(f"Döviz çekme hatası: {str(e)}")
        # Fallback değerler
        return {
            "USD": {"alis": 38.5, "satis": 38.7},
            "EUR": {"alis": 42.1, "satis": 42.4},
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "kaynak": "fallback"
        }

# ── Enflasyon Verisi (TÜİK) ───────────────────────────────────
def get_inflation_data() -> dict:
    """
    Güncel TÜFE verisi. TÜİK API olmadığı için
    son açıklanan verileri kullanıyoruz.
    Gün 4'te web scraping ile dinamik hale getirilebilir.
    """
    return {
        "aylik_tufe": 3.18,
        "yillik_tufe": 38.10,
        "donem": "Nisan 2026",
        "kategori": {
            "gida":     {"aylik": 3.2,  "yillik": 48.5},
            "ulasim":   {"aylik": 4.1,  "yillik": 61.2},
            "fatura":   {"aylik": 5.8,  "yillik": 78.4},
            "eglence":  {"aylik": 2.9,  "yillik": 38.7},
            "saglik":   {"aylik": 3.6,  "yillik": 52.1},
            "kira":     {"aylik": 6.2,  "yillik": 89.3},
            "diger":    {"aylik": 3.4,  "yillik": 45.0},
        },
        "kaynak": "TUIK"
    }

# ── Ekonomi Haberleri ─────────────────────────────────────────
def get_economic_news() -> list:
    """
    Güncel ekonomi haberlerini çeker.
    NewsAPI free tier: 100 istek/gün
    .env'e NEWS_API_KEY ekle: newsapi.org'dan ücretsiz alınır.
    """
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
        logger.error(f"Haber çekme hatası: {str(e)}")
        return get_fallback_news()

def get_fallback_news() -> list:
    """API yoksa genel bağlam haberleri."""
    return [
        {"baslik": "Merkez Bankası faiz kararını açıkladı", "kaynak": "Fallback", "tarih": "2026-05-13"},
        {"baslik": "Dolar/TL yüksek seyrediyor", "kaynak": "Fallback", "tarih": "2026-05-13"},
        {"baslik": "Yakıt fiyatlarına zam beklentisi", "kaynak": "Fallback", "tarih": "2026-05-13"},
    ]

# ── Ana Fonksiyon ─────────────────────────────────────────────
def get_market_context() -> dict:
    """Tüm piyasa bağlamını tek seferde toplar."""
    logger.info("Piyasa verileri çekiliyor")

    rates = get_exchange_rates()
    inflation = get_inflation_data()
    news = get_economic_news()

    context = {
        "doviz": rates,
        "enflasyon": inflation,
        "haberler": news,
        "ozet": {
            "usd_tl": rates.get("USD", {}).get("satis", 38.7),
            "eur_tl": rates.get("EUR", {}).get("satis", 42.4),
            "aylik_tufe": inflation["aylik_tufe"],
            "yillik_tufe": inflation["yillik_tufe"],
        }
    }

    logger.info(f"USD/TL: {context['ozet']['usd_tl']}")
    logger.info(f"Yıllık TÜFE: %{context['ozet']['yillik_tufe']}")
    return context


if __name__ == "__main__":
    context = get_market_context()

    print("\n--- DÖVİZ KURLARI ---")
    for kod, deger in context["doviz"].items():
        if isinstance(deger, dict):
            print(f"  {kod}: {deger.get('satis', deger.get('alis', '-'))} TL")

    print("\n--- ENFLASYON ---")
    print(f"  Aylık TÜFE : %{context['enflasyon']['aylik_tufe']}")
    print(f"  Yıllık TÜFE: %{context['enflasyon']['yillik_tufe']}")

    print("\n--- SON HABERLER ---")
    for h in context["haberler"]:
        print(f"  [{h['tarih']}] {h['baslik']}")