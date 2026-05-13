from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "finsight_transactions")
VECTOR_SIZE = 768

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

def init_collection():
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"Koleksiyon oluşturuldu: {COLLECTION_NAME}")
    else:
        print(f"Koleksiyon zaten var: {COLLECTION_NAME}")

    return client

def get_embedding(text: str) -> list:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result["embedding"]

if __name__ == "__main__":
    client = init_collection()
    info = client.get_collection(COLLECTION_NAME)
    print(f"Qdrant OK — vektör boyutu: {info.config.params.vectors.size}")