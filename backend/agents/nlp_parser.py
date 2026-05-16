import json
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
from utils.gemini import generate_with_retry
from utils.sanitizer import sanitize_text

logger = setup_logger("nlp_parser")

NLP_PROMPT = """
Kullanıcı doğal dille bir harcama veya gelir işlemi tanımladı.
Bunu aşağıdaki JSON formatına çevir:

{
  "tarih": "YYYY-MM-DD (bugünün tarihini kullan eğer belirtilmemişse: 2026-05-16)",
  "aciklama": "kısa açıklama",
  "tutar": 0.0,
  "tur": "gider veya gelir",
  "kategori": "gida/ulasim/fatura/eglence/saglik/kira/maas/diger",
  "yer": "yer adı varsa yaz, yoksa null",
  "guven": "yüksek/orta/düşük"
}

Kategori kuralları:
- Kafe, restoran, yemek → eglence
- Market, manav, fırın → gida
- Akaryakıt, otobüs, metro, taksi → ulasim
- Elektrik, su, doğalgaz, internet → fatura
- Eczane, doktor, hastane → saglik
- Netflix, Spotify, oyun → eglence
- Maaş, ücret, freelance → maas
- Kira → kira

SADECE JSON döndür. Başka hiçbir şey yazma.

Kullanıcı girişi:
"""

def parse_natural_language(text: str) -> dict:
    """
    Doğal dil harcama girişini yapılandırılmış veriye çevirir.
    Örnek: "Dün Kadıköy'de kafede 450 TL ödedim"
    """
    clean_text = sanitize_text(text, "nlp_input")
    logger.info(f"NLP parse başladı: '{clean_text[:50]}'")

    prompt = NLP_PROMPT + clean_text

    raw = generate_with_retry(prompt, use_system_prompt=False)

    # JSON temizle
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    logger.info(
        f"NLP parse tamamlandı: {result.get('aciklama')} — "
        f"{result.get('tutar')} TL — {result.get('kategori')}"
    )
    return result


def save_nlp_transaction(parsed: dict, session_id: str) -> bool:
    """Parse edilen işlemi Qdrant'a kaydeder."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
        from utils.gemini import get_embedding
        import uuid as uuid_lib
        from dotenv import load_dotenv
        load_dotenv()

        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )

        collection = os.getenv("QDRANT_COLLECTION", "finsight_transactions")
        text = (
            f"{parsed['tarih']} {parsed['aciklama']} "
            f"{parsed['tutar']} TL {parsed['kategori']}"
        )
        vector = get_embedding(text)

        point = PointStruct(
            id=str(uuid_lib.uuid4()),
            vector=vector,
            payload={
                "session_id": session_id,
                "tarih": parsed["tarih"],
                "aciklama": parsed["aciklama"],
                "tutar": -abs(parsed["tutar"]) if parsed["tur"] == "gider" else abs(parsed["tutar"]),
                "tur": parsed["tur"],
                "kategori": parsed["kategori"],
                "kaynak": "nlp",
            }
        )

        qdrant.upsert(collection_name=collection, points=[point])
        logger.info(f"NLP işlemi Qdrant'a kaydedildi: {parsed['aciklama']}")
        return True

    except Exception as e:
        logger.error(f"NLP kayıt hatası: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    testler = [
        "Dün Kadıköy'de bir kafede 450 TL ödedim",
        "Bu sabah Migros'tan 380 TL market alışverişi yaptım",
        "Shell'den 1200 TL benzin aldım",
        "Netflix aboneliği 349 TL çekti",
        "Bugün 42000 TL maaşım yattı",
        "Geçen hafta doktora 600 TL ödedim",
    ]

    print("NLP Parser Testi")
    print("=" * 60)

    for test in testler:
        print(f"\nGiriş  : {test}")
        result = parse_natural_language(test)
        print(f"Tarih  : {result.get('tarih')}")
        print(f"Açıklama: {result.get('aciklama')}")
        print(f"Tutar  : {result.get('tutar')} TL")
        print(f"Kategori: {result.get('kategori')}")
        print(f"Güven  : {result.get('guven')}")
        print("-" * 40)