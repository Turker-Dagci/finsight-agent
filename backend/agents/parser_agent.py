import os
import json
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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


if __name__ == "__main__":
    result = parse_pdf("data/samples/demo_ekstre.pdf")
    
    print("\n--- PARSE SONUCU ---")
    print(f"Hesap Sahibi : {result.get('hesap_sahibi')}")
    print(f"Dönem        : {result.get('donem')}")
    print(f"Toplam Gelir : {result.get('toplam_gelir')} TL")
    print(f"Toplam Gider : {result.get('toplam_gider')} TL")
    print(f"İşlem Sayısı : {len(result.get('islemler', []))}")
    print("\nİlk 3 işlem:")
    for i in result.get('islemler', [])[:3]:
        print(f"  {i['tarih']} | {i['aciklama'][:30]:30} | {i['tutar']:>10} TL | {i['kategori']}")