import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
from utils.gemini import generate_with_retry

logger = setup_logger("monthly_summary")

def generate_monthly_summary(
    categories: dict,
    parsed_summary: dict,
    inflation_analysis: dict,
    anomalies: list,
    subscriptions: list,
    health_score: dict
) -> str:
    """
    Copilot tarzı aylık sade dil özeti.
    Kullanıcı tek bakışta 'bu ay ne oldu' anlasın.
    """
    gelir = parsed_summary.get("toplam_gelir", 0) or 0
    gider = parsed_summary.get("toplam_gider", 0) or 0
    tasarruf = gelir - gider
    tasarruf_orani = (tasarruf / gelir * 100) if gelir > 0 else 0

    en_buyuk_kategori = max(categories, key=categories.get) if categories else "bilinmiyor"
    en_buyuk_tutar = categories.get(en_buyuk_kategori, 0)

    toplam_vergi_kayip = sum(
        v.get("kayip", 0) for v in inflation_analysis.values()
    )

    prompt = f"""
Aşağıdaki finansal verileri kullanarak kullanıcıya 3-4 cümlelik, 
sade ve anlaşılır bir aylık özet yaz. Teknik terim kullanma.
Sanki bir arkadaşın ona bu ayı özetliyor gibi yaz.
Türkçe yaz.

VERİLER:
- Toplam gelir: {gelir:,.0f} TL
- Toplam gider: {gider:,.0f} TL  
- Net tasarruf: {tasarruf:,.0f} TL (%{tasarruf_orani:.1f})
- En büyük harcama: {en_buyuk_kategori} ({en_buyuk_tutar:,.0f} TL)
- Enflasyon nedeniyle satın alma gücü kaybı: {toplam_vergi_kayip:,.0f} TL
- Anomali sayısı: {len(anomalies)}
- Abonelik sayısı: {len(subscriptions)}
- Finansal sağlık skoru: {health_score.get('toplam_skor', 0)}/100 ({health_score.get('seviye', '')})

ÖRNEK ÇIKTI TARZI:
"Bu ay toplam X TL harcadın ve Y TL tasarruf etmeyi başardın — 
bu geçen aya göre iyi bir performans. En büyük gider kalemin kira 
oldu, bu beklenen bir durum. Ancak enflasyon nedeniyle Z TL 
satın alma gücü kaybettiğini de unutma."

SADECE özet metni yaz, başka bir şey ekleme.
"""

    summary = generate_with_retry(prompt, use_system_prompt=False)
    logger.info("Aylık özet üretildi")
    return summary


if __name__ == "__main__":
    test_result = generate_monthly_summary(
        categories={"kira": 12000, "gida": 5411, "ulasim": 6450},
        parsed_summary={"toplam_gelir": 42000, "toplam_gider": 35994},
        inflation_analysis={
            "kira": {"kayip": 700},
            "ulasim": {"kayip": 255},
        },
        anomalies=["Netflix iki kez çekildi"],
        subscriptions=[{"aciklama": "Netflix"}, {"aciklama": "Spotify"}],
        health_score={"toplam_skor": 66, "seviye": "Orta"}
    )
    print(test_result)