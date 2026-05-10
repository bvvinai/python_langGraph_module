from __future__ import annotations

import os

from app.core.config import Settings
from app.domain.ports import VectorStore
from app.vectordb.embedding import (
    EmbeddingModel,
    HashEmbeddingModel,
    OllamaEmbeddingModel,
    OpenAICompatibleEmbeddingModel,
)
from app.vectordb.noop import NoopVectorStore
from app.vectordb.qdrant import QdrantVectorStore
from app.vectordb.registry import EmbeddingConfig, load_embedding_registry


class VectorStoreFactory:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._instance: VectorStore | None = None
        registry = load_embedding_registry(self.settings.embeddings_config_path)
        self._embedding_registry = {item.name: item for item in registry.embeddings if item.enabled}

    def get(self) -> VectorStore:
        if self._instance is not None:
            return self._instance

        if not self.settings.vector_db_enabled:
            self._instance = NoopVectorStore()
            return self._instance

        if self.settings.vector_db_provider == "qdrant":
            api_key = os.getenv(self.settings.qdrant_api_key_env, "") if self.settings.qdrant_api_key_env else ""
            embedding_model = self._build_embedding_model()
            self._instance = QdrantVectorStore(
                base_url=self.settings.qdrant_url,
                api_key=api_key or None,
                timeout_seconds=self.settings.qdrant_timeout_seconds,
                distance=self.settings.qdrant_distance,
                embedding_model=embedding_model,
            )
            return self._instance

        self._instance = NoopVectorStore()
        return self._instance

    def _build_embedding_model(self) -> EmbeddingModel:
        profile = self._embedding_registry.get(self.settings.embedding_profile)
        if profile is not None:
            return self._build_embedding_model_from_profile(profile)

        return self._build_embedding_model_from_legacy_settings()

    def _build_embedding_model_from_profile(self, profile: EmbeddingConfig) -> EmbeddingModel:
        if profile.type == "openai_compatible":
            return OpenAICompatibleEmbeddingModel(
                base_url=profile.base_url or self.settings.embedding_base_url,
                model=profile.model or self.settings.embedding_model,
                timeout_seconds=profile.timeout_seconds,
                api_key_env=profile.api_key_env,
                api_key_prefix=profile.api_key_prefix,
                endpoint_path=profile.endpoint_path or "/v1/embeddings",
                extra_headers=profile.extra_headers,
            )

        if profile.type == "ollama":
            return OllamaEmbeddingModel(
                base_url=profile.base_url or self.settings.embedding_base_url,
                model=profile.model or self.settings.embedding_model,
                timeout_seconds=profile.timeout_seconds,
                endpoint_path=profile.endpoint_path or "/api/embeddings",
            )

        vector_size = profile.vector_size or self.settings.vector_embedding_size
        return HashEmbeddingModel(size=vector_size)

    def _build_embedding_model_from_legacy_settings(self) -> EmbeddingModel:
        provider = self.settings.embedding_provider

        if provider == "openai_compatible":
            return OpenAICompatibleEmbeddingModel(
                base_url=self.settings.embedding_base_url,
                model=self.settings.embedding_model,
                timeout_seconds=self.settings.embedding_timeout_seconds,
                api_key_env=self.settings.embedding_api_key_env,
                api_key_prefix=self.settings.embedding_api_key_prefix,
                endpoint_path=self.settings.embedding_endpoint_path,
            )

        if provider == "ollama":
            return OllamaEmbeddingModel(
                base_url=self.settings.embedding_base_url,
                model=self.settings.embedding_model,
                timeout_seconds=self.settings.embedding_timeout_seconds,
                endpoint_path=self.settings.embedding_endpoint_path,
            )

        return HashEmbeddingModel(size=self.settings.vector_embedding_size)
