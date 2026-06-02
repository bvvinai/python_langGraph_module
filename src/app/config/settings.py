from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="langgraph-ai-backend", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    enable_rest: bool = Field(default=True, alias="ENABLE_REST")
    enable_websocket: bool = Field(default=True, alias="ENABLE_WEBSOCKET")
    enable_grpc: bool = Field(default=False, alias="ENABLE_GRPC")
    enable_ingestion: bool = Field(default=True, alias="ENABLE_INGESTION")
    enable_vectordb: bool = Field(default=True, alias="ENABLE_VECTORDB")
    enable_graphdb: bool = Field(default=False, alias="ENABLE_GRAPHDB")

    default_llm_model: str = Field(default="gpt-4o-mini", alias="DEFAULT_LLM_MODEL")
    llm_provider_config_path: str = Field(
        default="src/app/config/llm_providers.json",
        validation_alias=AliasChoices("LLM_PROVIDER_CONFIG_PATH", "LLM_MODEL_CONFIG_PATH"),
        serialization_alias="LLM_PROVIDER_CONFIG_PATH",
    )
    embedding_provider_config_path: str = Field(
        default="src/app/config/embeddings.json",
        validation_alias=AliasChoices(
            "EMBEDDING_PROVIDER_CONFIG_PATH",
            "EMBEDDING_MODEL_CONFIG_PATH",
        ),
        serialization_alias="EMBEDDING_PROVIDER_CONFIG_PATH",
    )
    default_embedding_provider: str = Field(default="openai", alias="DEFAULT_EMBEDDING_PROVIDER")
    default_embedding_model: str = Field(
        default="text-embedding-3-small", alias="DEFAULT_EMBEDDING_MODEL"
    )
    default_vector_store: str = Field(default="chroma", alias="DEFAULT_VECTOR_STORE")
    default_vector_collection: str = Field(default="documents", alias="DEFAULT_VECTOR_COLLECTION")

    enable_embedding_openai: bool = Field(default=True, alias="ENABLE_EMBEDDING_OPENAI")
    enable_embedding_ollama: bool = Field(default=True, alias="ENABLE_EMBEDDING_OLLAMA")

    enable_vector_qdrant: bool = Field(default=True, alias="ENABLE_VECTOR_QDRANT")
    enable_vector_chroma: bool = Field(default=True, alias="ENABLE_VECTOR_CHROMA")
    enable_graph_neo4j: bool = Field(default=True, alias="ENABLE_GRAPH_NEO4J")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_genai_api_key: str | None = Field(default=None, alias="GOOGLE_GENAI_API_KEY")
    mistral_api_key: str | None = Field(default=None, alias="MISTRAL_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_default_collection: str = Field(default="documents", alias="QDRANT_DEFAULT_COLLECTION")

    chroma_persist_directory: str = Field(default=".chroma", alias="CHROMA_PERSIST_DIRECTORY")
    chroma_host: str | None = Field(default=None, alias="CHROMA_HOST")
    chroma_port: int = Field(default=8000, alias="CHROMA_PORT")
    chroma_ssl: bool = Field(default=False, alias="CHROMA_SSL")
    chroma_distance_metric: str = Field(default="cosine", alias="CHROMA_DISTANCE_METRIC")

    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str | None = Field(default=None, alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    max_concurrent_embeddings: int = Field(default=32, alias="MAX_CONCURRENT_EMBEDDINGS")
    default_chunk_size: int = Field(default=1200, alias="DEFAULT_CHUNK_SIZE")
    default_chunk_overlap: int = Field(default=200, alias="DEFAULT_CHUNK_OVERLAP")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()