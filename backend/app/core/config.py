import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Disruptive Architectures RAG Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Chave de API e modelos do Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-2"

    # Caminhos para dados do RAG
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    KNOWLEDGE_BASE_PATH: Path = BASE_DIR / "data" / "knowledge_base.json"
    EMBEDDINGS_PATH: Path = BASE_DIR / "data" / "embeddings.npy"

    # URL base da documentação MkDocs
    BASE_DOCS_URL: str = "https://enzookuizumifiap.github.io/DisruptiveArchitecturesCheckpoint"

    # Parâmetros de Recuperação (RAG)
    TOP_K_RESULTS: int = 5
    VECTOR_WEIGHT: float = 0.5
    BM25_WEIGHT: float = 0.5
    SIMILARITY_THRESHOLD: float = 0.35

    # Configuração de CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = [
            Path(__file__).resolve().parent.parent.parent / ".env",
            Path.cwd() / ".env",
            Path.cwd() / "backend" / ".env"
        ]
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
