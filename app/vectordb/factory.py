from __future__ import annotations

import os

from app.core.config import Settings
from app.vectordb.embedding import (
    EmbeddingModel,
    HashEmbeddingModel,
    OllamaEmbeddingModel,
    OpenAICompatibleEmbeddingModel,
)
from app.vectordb.qdrant import QdrantVectorStore
from app.vectordb.registry import EmbeddingConfig, load_embedding_registry


def build_vector_store(settings: Settings) -> QdrantVectorStore:
    embedding_model = _build_embedding_model(settings)
    api_key = os.getenv(settings.qdrant_api_key_env, "") if settings.qdrant_api_key_env else ""
    return QdrantVectorStore(
        base_url=settings.qdrant_url,
        api_key=api_key or None,
        timeout_seconds=settings.qdrant_timeout_seconds,
        distance=settings.qdrant_distance,
        embedding_model=embedding_model,
    )


def _build_embedding_model(settings: Settings) -> EmbeddingModel:
    registry = load_embedding_registry(settings.embeddings_config_path)
    enabled = {item.name: item for item in registry.embeddings if item.enabled}
    profile = enabled.get(settings.embedding_profile)
    if profile is not None:
        return _build_embedding_model_from_profile(profile, settings)
    return _build_embedding_model_from_legacy_settings(settings)


def _build_embedding_model_from_profile(profile: EmbeddingConfig, settings: Settings) -> EmbeddingModel:
    if profile.type == "openai_compatible":
        return OpenAICompatibleEmbeddingModel(
            base_url=profile.base_url or settings.embedding_base_url,
            model=profile.model or settings.embedding_model,
            timeout_seconds=profile.timeout_seconds,
            api_key_env=profile.api_key_env,
            api_key_prefix=profile.api_key_prefix,
            endpoint_path=profile.endpoint_path or "/v1/embeddings",
            extra_headers=profile.extra_headers,
        )

    if profile.type == "ollama":
        return OllamaEmbeddingModel(
            base_url=profile.base_url or settings.embedding_base_url,
            model=profile.model or settings.embedding_model,
            timeout_seconds=profile.timeout_seconds,
            endpoint_path=profile.endpoint_path or "/api/embeddings",
        )

    vector_size = profile.vector_size or settings.vector_embedding_size
    return HashEmbeddingModel(size=vector_size)


def _build_embedding_model_from_legacy_settings(settings: Settings) -> EmbeddingModel:
    provider = settings.embedding_provider

    if provider == "openai_compatible":
        return OpenAICompatibleEmbeddingModel(
            base_url=settings.embedding_base_url,
            model=settings.embedding_model,
            timeout_seconds=settings.embedding_timeout_seconds,
            api_key_env=settings.embedding_api_key_env,
            api_key_prefix=settings.embedding_api_key_prefix,
            endpoint_path=settings.embedding_endpoint_path,
        )

    if provider == "ollama":
        return OllamaEmbeddingModel(
            base_url=settings.embedding_base_url,
            model=settings.embedding_model,
            timeout_seconds=settings.embedding_timeout_seconds,
            endpoint_path=settings.embedding_endpoint_path,
        )

    return HashEmbeddingModel(size=settings.vector_embedding_size)
