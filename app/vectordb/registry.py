from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.utils import resolve_env_vars


class EmbeddingConfig(BaseModel):
    name: str
    type: str = Field(description="openai_compatible or ollama")
    enabled: bool = True
    model: str | None = None
    base_url: str | None = None
    endpoint_path: str | None = None
    timeout_seconds: float = 15.0
    api_key_env: str | None = None
    api_key_prefix: str = "Bearer"
    vector_size: int | None = None
    extra_headers: dict[str, str] = Field(default_factory=dict)


class EmbeddingRegistry(BaseModel):
    embeddings: list[EmbeddingConfig] = Field(default_factory=list)


def load_embedding_registry(config_path: str) -> EmbeddingRegistry:
    path = Path(config_path)
    if not path.exists():
        return EmbeddingRegistry(embeddings=[])

    data = resolve_env_vars(json.loads(path.read_text(encoding="utf-8")))
    items = [EmbeddingConfig(**item) for item in data.get("embeddings", [])]
    return EmbeddingRegistry(embeddings=items)
