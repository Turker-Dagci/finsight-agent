from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    gemini_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str = "finsight_transactions"
    environment: str = "development"
    log_level: str = "INFO"
    max_file_size_mb: int = 10
    rate_limit_per_minute: int = 10
    vector_size: int = 768
    embedding_model: str = "gemini-embedding-001"
    generation_model: str = "gemini-2.5-flash"

settings = Settings()

if __name__ == "__main__":
    print(f"Ortam       : {settings.environment}")
    print(f"Koleksiyon  : {settings.qdrant_collection}")
    print(f"Vektör boyut: {settings.vector_size}")
    print(f"Model       : {settings.generation_model}")