import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
import uuid

load_dotenv()
logger = setup_logger("category_learning")

LEARNING_COLLECTION = "finsight_category_rules"

def get_qdrant_client():
    return QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

def init_learning_collection():
    """Öğrenme koleksiyonunu başlat."""
    from qdrant_client.models import Distance, VectorParams
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if LEARNING_COLLECTION not in collections:
        client.create_collection(
            collection_name=LEARNING_COLLECTION,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        logger.info(f"Öğrenme koleksiyonu oluşturuldu: {LEARNING_COLLECTION}")
    return client

def save_category_correction(
    aciklama: str,
    eski_kategori: str,
    yeni_kategori: str
):
    """
    Kullanıcının düzelttiği kategoriyi kaydeder.
    Bir dahaki sefere bu işlem doğru kategorize edilir.
    """
    from utils.gemini import get_embedding
    try:
        client = init_learning_collection()
        vector = get_embedding(aciklama)

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "aciklama": aciklama,
                "eski_kategori": eski_kategori,
                "dogru_kategori": yeni_kategori,
                "kayit_tarihi": str(__import__("datetime").datetime.now()),
            }
        )
        client.upsert(collection_name=LEARNING_COLLECTION, points=[point])
        logger.info(f"Kategori düzeltmesi kaydedildi: '{aciklama}' → {yeni_kategori}")
        return True
    except Exception as e:
        logger.error(f"Kategori kayıt hatası: {str(e)}")
        return False

def get_learned_category(aciklama: str) -> str | None:
    """
    Daha önce öğrenilmiş bir kategori var mı kontrol eder.
    Varsa döndürür, yoksa None.
    """
    from utils.gemini import get_embedding
    try:
        client = get_qdrant_client()
        collections = [c.name for c in client.get_collections().collections]
        if LEARNING_COLLECTION not in collections:
            return None

        vector = get_embedding(aciklama)
        results = client.search(
            collection_name=LEARNING_COLLECTION,
            query_vector=vector,
            limit=1,
            score_threshold=0.92
        )

        if results:
            kategori = results[0].payload.get("dogru_kategori")
            logger.info(f"Öğrenilmiş kategori bulundu: '{aciklama}' → {kategori}")
            return kategori
        return None
    except Exception as e:
        logger.error(f"Kategori arama hatası: {str(e)}")
        return None


if __name__ == "__main__":
    print("Kategori öğrenme sistemi testi")

    # Düzeltme kaydet
    save_category_correction(
        aciklama="Shell Yakıt İstasyonu",
        eski_kategori="diger",
        yeni_kategori="ulasim"
    )

    # Öğrenilmiş kategoriyi sorgula
    kategori = get_learned_category("Shell yakıt")
    print(f"Öğrenilmiş kategori: {kategori}")