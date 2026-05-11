from __future__ import annotations

import os

from app.core.config import Settings
from app.vectordb.embedding import (
    EmbeddingModel,
    OllamaEmbeddingModel,
    OpenAICompatibleEmbeddingModel,
)
from app.vectordb.qdrant import QdrantVectorStore
from app.vectordb.registry import EmbeddingConfig, load_embedding_registry

__all__ = ["build_vector_store"]


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
    if profile is None:
        raise RuntimeError(
            f"Embedding profile '{settings.embedding_profile}' not found in registry "
            f"'{settings.embeddings_config_path}'."
        )
    return _build_embedding_model_from_profile(profile)


def _build_embedding_model_from_profile(profile: EmbeddingConfig) -> EmbeddingModel:
    if profile.type == "openai_compatible":
        if not profile.base_url or not profile.model:
            raise RuntimeError(
                f"Profile '{profile.name}' of type 'openai_compatible' requires base_url and model."
            )
        return OpenAICompatibleEmbeddingModel(
            base_url=profile.base_url,
            model=profile.model,
            timeout_seconds=profile.timeout_seconds,
            api_key_env=profile.api_key_env,
            api_key_prefix=profile.api_key_prefix,
            endpoint_path=profile.endpoint_path or "/v1/embeddings",
            extra_headers=profile.extra_headers,
        )

    if profile.type == "ollama":
        if not profile.base_url or not profile.model:
            raise RuntimeError(
                f"Profile '{profile.name}' of type 'ollama' requires base_url and model."
            )
        return OllamaEmbeddingModel(
            base_url=profile.base_url,
            model=profile.model,
            timeout_seconds=profile.timeout_seconds,
            endpoint_path=profile.endpoint_path or "/api/embeddings",
        )

    raise RuntimeError(f"Profile '{profile.name}' has unsupported embedding type '{profile.type}'.")
