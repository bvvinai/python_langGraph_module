from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    name: str
    type: str = Field(description="anthropic, openai_compatible, or ollama")
    enabled: bool = True
    base_url: str | None = None
    api_key_env: str | None = None
    api_key_prefix: str = "Bearer"
    endpoint_path: str | None = None
    default_model: str | None = None
    timeout_seconds: float = 30.0
    extra_headers: dict[str, str] = Field(default_factory=dict)


class ProviderRegistry(BaseModel):
    providers: list[ProviderConfig]


def _resolve_env_vars(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _resolve_env_vars(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_name = value[2:-1]
        return os.getenv(env_name, "")
    return value


def load_provider_registry(config_path: str) -> ProviderRegistry:
    path = Path(config_path)
    if not path.exists():
        return ProviderRegistry(providers=[])

    data = _resolve_env_vars(json.loads(path.read_text(encoding="utf-8")))
    providers = [ProviderConfig(**item) for item in data.get("providers", [])]
    return ProviderRegistry(providers=providers)
