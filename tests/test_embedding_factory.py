from __future__ import annotations

import json
from pathlib import Path

from app.vectordb.embedding import HashEmbeddingModel, OllamaEmbeddingModel, OpenAICompatibleEmbeddingModel
from app.vectordb.factory import build_vector_store
from app.vectordb.qdrant import QdrantVectorStore


class FakeSettings:
    vector_embedding_size = 128

    qdrant_url = "http://qdrant:6333"
    qdrant_api_key_env = None
    qdrant_timeout_seconds = 5.0
    qdrant_distance = "Cosine"

    embeddings_config_path = ""
    embedding_profile = "hash-local"


def _write_embeddings_config(path: Path) -> None:
    payload = {
        "embeddings": [
            {"name": "hash-local", "type": "hash", "vector_size": 128},
            {
                "name": "openai-small",
                "type": "openai_compatible",
                "base_url": "https://api.openai.com",
                "endpoint_path": "/v1/embeddings",
                "model": "text-embedding-3-small",
            },
            {
                "name": "ollama-nomic",
                "type": "ollama",
                "base_url": "http://ollama:11434",
                "endpoint_path": "/api/embeddings",
                "model": "nomic-embed-text",
            },
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_factory_uses_hash_embedding_by_default(tmp_path: Path) -> None:
    config_path = tmp_path / "embeddings.json"
    _write_embeddings_config(config_path)
    settings = FakeSettings()
    settings.embeddings_config_path = str(config_path)

    store = build_vector_store(settings)

    assert isinstance(store, QdrantVectorStore)
    assert isinstance(store.embedding_model, HashEmbeddingModel)


def test_factory_can_use_openai_compatible_embedding(tmp_path: Path) -> None:
    config_path = tmp_path / "embeddings.json"
    _write_embeddings_config(config_path)
    settings = FakeSettings()
    settings.embeddings_config_path = str(config_path)
    settings.embedding_profile = "openai-small"

    store = build_vector_store(settings)

    assert isinstance(store, QdrantVectorStore)
    assert isinstance(store.embedding_model, OpenAICompatibleEmbeddingModel)


def test_factory_can_use_ollama_embedding(tmp_path: Path) -> None:
    config_path = tmp_path / "embeddings.json"
    _write_embeddings_config(config_path)
    settings = FakeSettings()
    settings.embeddings_config_path = str(config_path)
    settings.embedding_profile = "ollama-nomic"

    store = build_vector_store(settings)

    assert isinstance(store, QdrantVectorStore)
    assert isinstance(store.embedding_model, OllamaEmbeddingModel)
