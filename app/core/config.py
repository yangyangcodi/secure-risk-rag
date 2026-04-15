from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_env: str = "dev"

    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Model / AI
    model_provider: str = "vertex"
    embedding_model: str
    gen_model: str

    # Vertex AI (or other providers)
    vertex_project_id: str
    vertex_location: str = "us-central1"

    # Vector store
    vector_index_path: str = "./app/data/faiss.index"
    doc_store_path: str = "./app/data/docstore.json"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Cache settings so it's only loaded once
@lru_cache()
def get_settings():
    return Settings()


# Optional: quick access
settings = get_settings()
