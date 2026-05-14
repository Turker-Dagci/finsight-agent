from google import genai
from google.genai import types as genai_types
import time
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger("gemini")

FINSIGHT_SYSTEM_PROMPT = """
Sen FinSight Agent'ın entegre finans danışmanısın.
FinSight, Türkiye'deki KOBİ'ler ve bireyler için
geliştirilmiş çok-ajanlı bir yapay zeka finansal
analiz sistemidir.

SİSTEM MİMARİSİ:
- Parser Agent: PDF banka ekstresi ve faturaları
  Gemini Vision ile parse eder
- Analyst Agent: Harcamaları kategorize eder,
  enflasyon düzeltmesi, Vergi X-Ray ve anomali
  tespiti yapar
- Advisory Agent: TCMB'den canlı döviz verileri,
  güncel ekonomi haberleri ve kullanıcı profilini
  birleştirerek kişiselleştirilmiş tavsiye üretir

TEMEL ÖZELLİKLER:
1. Enflasyon Düzeltmesi: TÜİK TÜFE verileriyle
   nominal harcamaları reel değere çevirir
2. Vergi X-Ray: KDV ve ÖTV dahil gizli vergi
   yükünü kategori bazlı hesaplar
3. Abonelik Dedektörü: Tekrar eden ödemeleri ve
   döviz bazlı aboneliklerin TL artışını takip eder
4. Döviz Kalkanı: TCMB canlı kurlarla aylık
   harcamanın USD/EUR karşılığını hesaplar
5. Proaktif Uyarı: Kullanıcı sormadan bütçe
   aşımı, yüksek enflasyon kategorileri ve
   tasarruf oranı uyarısı üretir
6. Jeopolitik Risk Farkındalığı: Mevcut ekonomi
   haberleri bağlamında makroekonomik risklere
   dikkat çeker. Kullanıcıya olası etkiler
   hakkında farkındalık sunar.

TÜRK EKONOMİSİ BAĞLAMI:
- Yüksek enflasyon ortamı (yıllık %38+)
- Döviz kuru oynaklığı
- Yüksek dolaylı vergi yükü (KDV, ÖTV)
- KOBİ'lerin nakit akışı kırılganlığı

GÖREV TANIMI:
1. Türkiye ekonomik gerçekliğine uygun ol
2. Yatırım tavsiyesi değil finansal farkındalık
   sun. Doğru: "Döviz kurundaki oynaklık birikim
   değerinizi etkiliyor — uzmanla değerlendirin."
   Yanlış: "Dolar alın."
3. Somut, ölçülebilir, eyleme dönüştürülebilir
   öneriler ver
4. Yanıtlarını FinSight özellikleriyle ilişkilendir

SINIRLAR:
- Kesin yatırım kararı verme
- Garanti getiri vaat etme
- Hukuki veya vergi danışmanlığı yapma

FORMAT:
- Türkçe yanıt ver
- Standart sorular 200-250 kelime,
  karmaşık analizlerde 400 kelimeye kadar
- Madde madde yaz
"""

def get_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_with_retry(
    prompt: str,
    model: str = "gemini-2.5-flash",
    max_retries: int = 3,
    use_system_prompt: bool = True
) -> str:
    """Retry mekanizmalı Gemini çağrısı."""
    client = get_client()

    for attempt in range(max_retries):
        try:
            config = None
            if use_system_prompt:
                config = genai_types.GenerateContentConfig(
                    system_instruction=FINSIGHT_SYSTEM_PROMPT
                )

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )
            return response.text

        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "UNAVAILABLE" in error_str:
                wait = 2 ** attempt  # 1, 2, 4 saniye
                logger.warning(f"Gemini meşgul, {wait}s bekleyip tekrar deneniyor... ({attempt+1}/{max_retries})")
                time.sleep(wait)
            elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait = 5 * (attempt + 1)
                logger.warning(f"Rate limit, {wait}s bekleyip tekrar deneniyor... ({attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                logger.error(f"Gemini hatası: {error_str}")
                raise

    kullanici_mesaji = "Analiz geçici olarak kullanılamıyor. Lütfen tekrar deneyin."
    logger.error("Tüm retry denemeleri başarısız.")
    return kullanici_mesaji

def generate_vision_with_retry(
    prompt: str,
    file_bytes: bytes,
    mime_type: str = "application/pdf",
    max_retries: int = 3
) -> str:
    """Vision için retry mekanizmalı Gemini çağrısı."""
    client = get_client()

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    genai_types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type
                    ),
                    prompt
                ]
            )
            return response.text

        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "UNAVAILABLE" in error_str:
                wait = 2 ** attempt
                logger.warning(f"Vision API meşgul, {wait}s bekleniyor... ({attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                logger.error(f"Vision hatası: {error_str}")
                raise

    return ""

def get_embedding(text: str) -> list:
    """Merkezi embedding fonksiyonu — 768 boyut sabit."""
    client = get_client()
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=genai_types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=768
        )
    )
    return response.embeddings[0].values

if __name__ == "__main__":
    result = generate_with_retry("Merhaba, tek cümleyle kendini tanıt.")
    print("Gemini OK:", result[:100])