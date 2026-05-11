from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="LangGraph FastAPI Starter", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    default_provider: str = Field(default="openai", alias="DEFAULT_PROVIDER")
    providers_config_path: str = Field(default="config/providers.json", alias="PROVIDERS_CONFIG_PATH")

    vector_db_enabled: bool = Field(default=True, alias="VECTOR_DB_ENABLED")
    vector_db_provider: str = Field(default="qdrant", alias="VECTOR_DB_PROVIDER")
    vector_db_default_collection: str = Field(default="knowledge_base", alias="VECTOR_DB_DEFAULT_COLLECTION")
    vector_embedding_size: int = Field(default=256, alias="VECTOR_EMBEDDING_SIZE")
    rag_mode: str = Field(default="graph_rag", alias="RAG_MODE")

    embeddings_config_path: str = Field(default="config/embeddings.json", alias="EMBEDDINGS_CONFIG_PATH")
    embedding_profile: str = Field(default="hash-local", alias="EMBEDDING_PROFILE")

    # Legacy embedding settings are kept as a fallback if profile lookup fails.
    embedding_provider: str = Field(default="hash", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="EMBEDDING_MODEL")
    embedding_base_url: str = Field(default="https://api.openai.com", alias="EMBEDDING_BASE_URL")
    embedding_api_key_env: str | None = Field(default="OPENAI_API_KEY", alias="EMBEDDING_API_KEY_ENV")
    embedding_api_key_prefix: str = Field(default="Bearer", alias="EMBEDDING_API_KEY_PREFIX")
    embedding_endpoint_path: str = Field(default="/v1/embeddings", alias="EMBEDDING_ENDPOINT_PATH")
    embedding_timeout_seconds: float = Field(default=15.0, alias="EMBEDDING_TIMEOUT_SECONDS")

    qdrant_url: str = Field(default="http://qdrant:6333", alias="QDRANT_URL")
    qdrant_api_key_env: str | None = Field(default="QDRANT_API_KEY", alias="QDRANT_API_KEY_ENV")
    qdrant_timeout_seconds: float = Field(default=10.0, alias="QDRANT_TIMEOUT_SECONDS")
    qdrant_distance: str = Field(default="Cosine", alias="QDRANT_DISTANCE")

    graph_db_enabled: bool = Field(default=False, alias="GRAPH_DB_ENABLED")
    graph_db_provider: str = Field(default="neo4j", alias="GRAPH_DB_PROVIDER")
    neo4j_uri: str = Field(default="bolt://neo4j:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password_env: str | None = Field(default="NEO4J_PASSWORD", alias="NEO4J_PASSWORD_ENV")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    graph_rag_max_neighbors: int = Field(default=10, alias="GRAPH_RAG_MAX_NEIGHBORS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
