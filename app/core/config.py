from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_env: str = "dev"

    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Model / AI
    model_provider: str = "mock"
    embedding_model: str = "all-MiniLM-L6-v2"
    gen_model: str = "claude-opus-4-6"

    # Anthropic
    anthropic_api_key: str = ""

    # Vertex AI
    vertex_project_id: str = ""
    vertex_location: str = "us-central1"

    # Vector store
    vector_index_path: str = "./app/data/faiss.index"
    doc_store_path: str = "./app/data/docstore.json"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Cache settings so it's only loaded once
@lru_cache()
def get_settings():
    return Settings()


# Optional: quick access
settings = get_settings()
