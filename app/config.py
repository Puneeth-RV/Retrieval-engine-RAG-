from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys (required - set these in .env or environment)
    JINA_API_KEY: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    GROQ_API_KEY: str

    # Qdrant collection
    COLLECTION_NAME: str = "rag_documents"
    EMBEDDING_DIM: int = 768  # jina-embeddings-v2-base-en output dimension

    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Retrieval
    TOP_K: int = 5

    # Upload limits (protect free tier)
    MAX_FILE_SIZE_MB: int = 10
    MAX_FILES_PER_UPLOAD: int = 5

    # Jina
    JINA_MODEL: str = "jina-embeddings-v2-base-en"

    # Groq
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    MAX_TOKENS: int = 1024

    model_config = {"env_file": ".env"}


settings = Settings()
