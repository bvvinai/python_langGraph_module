from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    name: str
    type: str = Field(description="mock or openai_compatible")
    base_url: str | None = None
    api_key_env: str | None = None
    default_model: str | None = None
    timeout_seconds: float = 30.0
    extra_headers: dict[str, str] = Field(default_factory=dict)


class ProviderRegistry(BaseModel):
    providers: list[ProviderConfig]


def load_provider_registry(config_path: str) -> ProviderRegistry:
    path = Path(config_path)
    if not path.exists():
        return ProviderRegistry(providers=[ProviderConfig(name="mock", type="mock")])

    data = json.loads(path.read_text(encoding="utf-8"))
    providers = [ProviderConfig(**item) for item in data.get("providers", [])]
    if not providers:
        providers.append(ProviderConfig(name="mock", type="mock"))
    return ProviderRegistry(providers=providers)
