import os
import json
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from google.genai import types, types as genai_types
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

PARSE_PROMPT = """
Bu bir banka ekstresi veya fatura belgesidir. 
Belgedeki TÜM işlemleri aşağıdaki JSON formatında çıkar:

{
  "hesap_sahibi": "...",
  "donem": "...",
  "para_birimi": "TRY",
  "toplam_gelir": 0.0,
  "toplam_gider": 0.0,
  "islemler": [
    {
      "tarih": "YYYY-MM-DD",
      "aciklama": "...",
      "tutar": 0.0,
      "tur": "gelir veya gider",
      "kategori": "tahmin et: gida/ulasim/fatura/eglence/saglik/kira/maas/diger"
    }
  ]
}

Kategorileri şu kurallara göre belirle:
- Migros, CarrefourSA, A101, BİM, market → gida
- Shell, Opet, BP, yakıt → ulasim
- BEDAŞ, İGDAŞ, İSKİ, elektrik, doğalgaz, su → fatura
- Netflix, Spotify, Amazon, abonelik → eglence
- Kafe, sinema, bowling, restoran → eglence  
- Eczane, ilaç, hastane → saglik
- Kira → kira
- Maaş, ücret → maas
- Araç bakım, servis → ulasim

SADECE JSON döndür. Başka hiçbir şey yazma.
Türkçe karakterlere dikkat et.
Tutarları sayısal değer olarak ver (nokta ondalık ayraç).
"""

def parse_pdf(file_path: str) -> dict:
    """PDF dosyasını Gemini Vision ile parse eder."""
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    
    print(f"[Parser] PDF okundu: {len(pdf_bytes)} byte")
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=pdf_bytes,
                mime_type="application/pdf"
            ),
            PARSE_PROMPT
        ]
    )
    
    raw_text = response.text.strip()
    print(f"[Parser] Gemini yanıtı alındı: {len(raw_text)} karakter")
    
    # JSON temizle
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()
    
    result = json.loads(raw_text)
    print(f"[Parser] {len(result.get('islemler', []))} işlem parse edildi")
    
    return result

from google.genai import types as genai_types

def save_to_qdrant(parsed_data: dict, session_id: str) -> int:
    """Parse edilen işlemleri Qdrant'a kaydeder."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    import uuid as uuid_lib

    qdrant = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    collection = os.getenv("QDRANT_COLLECTION", "finsight_transactions")
    points = []

    for islem in parsed_data.get("islemler", []):
        # Embedding için metin oluştur
        text = f"{islem['tarih']} {islem['aciklama']} {islem['tutar']} TL {islem['kategori']}"

        # Gemini embedding
        embed_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        embed_response = embed_client.models.embed_content(
    model="gemini-embedding-001",
    contents=text,
    config=genai_types.EmbedContentConfig(
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=768
    )
)
        vector = embed_response.embeddings[0].values

        point = PointStruct(
            id=str(uuid_lib.uuid4()),
            vector=vector,
            payload={
                "session_id": session_id,
                "tarih": islem["tarih"],
                "aciklama": islem["aciklama"],
                "tutar": islem["tutar"],
                "tur": islem["tur"],
                "kategori": islem["kategori"],
                "hesap_sahibi": parsed_data.get("hesap_sahibi"),
                "donem": parsed_data.get("donem"),
            }
        )
        points.append(point)

    qdrant.upsert(collection_name=collection, points=points)
    print(f"[Parser] {len(points)} işlem Qdrant'a kaydedildi")
    return len(points)

if __name__ == "__main__":
    import uuid
    session = str(uuid.uuid4())
    
    result = parse_pdf("data/samples/demo_ekstre.pdf")
    
    print("\n--- PARSE SONUCU ---")
    print(f"Hesap Sahibi : {result.get('hesap_sahibi')}")
    print(f"Dönem        : {result.get('donem')}")
    print(f"Toplam Gelir : {result.get('toplam_gelir')} TL")
    print(f"Toplam Gider : {result.get('toplam_gider')} TL")
    print(f"İşlem Sayısı : {len(result.get('islemler', []))}")
    
    print("\n--- QDRANT'A YAZILIYOR ---")
    saved = save_to_qdrant(result, session)
    print(f"Kaydedilen : {saved} işlem")
    print(f"Session ID : {session}")