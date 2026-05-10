from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    name: str
    type: str = Field(description="hash, openai_compatible, or ollama")
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


def _resolve_env_vars(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _resolve_env_vars(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_name = value[2:-1]
        return os.getenv(env_name, "")
    return value


def load_embedding_registry(config_path: str) -> EmbeddingRegistry:
    path = Path(config_path)
    if not path.exists():
        return EmbeddingRegistry(embeddings=[])

    data = _resolve_env_vars(json.loads(path.read_text(encoding="utf-8")))
    items = [EmbeddingConfig(**item) for item in data.get("embeddings", [])]
    return EmbeddingRegistry(embeddings=items)
