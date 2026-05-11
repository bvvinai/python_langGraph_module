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

    default_provider: str = Field(default="ollama", alias="DEFAULT_PROVIDER")
    providers_config_path: str = Field(default="config/providers.json", alias="PROVIDERS_CONFIG_PATH")

    vector_db_enabled: bool = Field(default=True, alias="VECTOR_DB_ENABLED")
    vector_db_provider: str = Field(default="qdrant", alias="VECTOR_DB_PROVIDER")
    vector_db_default_collection: str = Field(default="knowledge_base", alias="VECTOR_DB_DEFAULT_COLLECTION")
    vector_embedding_size: int = Field(default=256, alias="VECTOR_EMBEDDING_SIZE")
    rag_mode: str = Field(default="graph_rag", alias="RAG_MODE")

    embeddings_config_path: str = Field(default="config/embeddings.json", alias="EMBEDDINGS_CONFIG_PATH")
    embedding_profile: str = Field(default="ollama-nomic-embed-text", alias="EMBEDDING_PROFILE")

    qdrant_url: str = Field(default="http://qdrant:6333", alias="QDRANT_URL")
    qdrant_api_key_env: str | None = Field(default="QDRANT_API_KEY", alias="QDRANT_API_KEY_ENV")
    qdrant_timeout_seconds: float = Field(default=10.0, alias="QDRANT_TIMEOUT_SECONDS")
    qdrant_distance: str = Field(default="Cosine", alias="QDRANT_DISTANCE")

    graph_db_enabled: bool = Field(default=True, alias="GRAPH_DB_ENABLED")
    graph_db_provider: str = Field(default="neo4j", alias="GRAPH_DB_PROVIDER")
    neo4j_uri: str = Field(default="bolt://neo4j:7687", alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    neo4j_password_env: str | None = Field(default="NEO4J_PASSWORD", alias="NEO4J_PASSWORD_ENV")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    graph_rag_max_neighbors: int = Field(default=10, alias="GRAPH_RAG_MAX_NEIGHBORS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
