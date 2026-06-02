from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import json
from pathlib import Path
from typing import Any


_PROJECT_ROOT = Path(__file__).resolve().parents[3]

_DEFAULT_CONFIG: dict[str, Any] = {
    "default_provider": "openai_default",
    "models": {
        "openai_default": {
            "enabled": True,
            "backend": "openai",
            "model": "text-embedding-3-small",
            "api_key_env": "OPENAI_API_KEY",
            "aliases": ["openai"],
        },
        "openai_large": {
            "enabled": True,
            "backend": "openai",
            "model": "text-embedding-3-large",
            "api_key_env": "OPENAI_API_KEY",
            "aliases": ["openai-large"],
        },
        "ollama_default": {
            "enabled": True,
            "backend": "ollama",
            "model": "nomic-embed-text",
            "base_url": "http://localhost:11434",
            "aliases": ["ollama", "local"],
        },
        "ollama_mxbai": {
            "enabled": True,
            "backend": "ollama",
            "model": "mxbai-embed-large",
            "base_url": "http://localhost:11434",
            "aliases": ["mxbai"],
        },
    },
}


@dataclass(frozen=True, slots=True)
class EmbeddingProviderEntry:
    name: str
    backend: str
    model: str | None = None
    base_url: str | None = None
    api_key_env: str | None = None
    enabled: bool = True
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EmbeddingProvidersConfig:
    default_provider: str
    providers: dict[str, EmbeddingProviderEntry] = field(default_factory=dict)
    alias_map: dict[str, str] = field(default_factory=dict)

    def resolve_provider(self, provider_name: str | None) -> str | None:
        if not provider_name:
            return None
        key = str(provider_name).strip().lower()
        if not key:
            return None
        if key in self.providers:
            return key
        return self.alias_map.get(key)

    def provider_enabled(self, provider_name: str | None) -> bool:
        resolved = self.resolve_provider(provider_name)
        if not resolved:
            return False
        entry = self.providers.get(resolved)
        return bool(entry and entry.enabled)

    def provider_entry(self, provider_name: str | None) -> EmbeddingProviderEntry | None:
        resolved = self.resolve_provider(provider_name)
        if not resolved:
            return None
        return self.providers.get(resolved)


def _normalize_str(value: Any) -> str:
    return str(value).strip().lower()


def _parse_provider(name: str, raw_provider: Any) -> EmbeddingProviderEntry:
    if not isinstance(raw_provider, dict):
        return EmbeddingProviderEntry(
            name=name,
            backend=name,
            model=None,
            enabled=bool(raw_provider),
            aliases=(),
        )

    aliases_raw = raw_provider.get("aliases", [])
    aliases: tuple[str, ...] = tuple(
        alias
        for alias in (_normalize_str(item) for item in aliases_raw if isinstance(item, str))
        if alias
    )
    backend_raw = raw_provider.get("backend") or raw_provider.get("provider") or name
    backend = _normalize_str(backend_raw)
    model_raw = raw_provider.get("model")
    model = str(model_raw).strip() if isinstance(model_raw, str) and model_raw.strip() else None
    base_url_raw = raw_provider.get("base_url")
    base_url = str(base_url_raw).strip() if isinstance(base_url_raw, str) and base_url_raw.strip() else None
    api_key_env_raw = raw_provider.get("api_key_env")
    api_key_env = (
        str(api_key_env_raw).strip() if isinstance(api_key_env_raw, str) and api_key_env_raw.strip() else None
    )
    enabled = bool(raw_provider.get("enabled", True))
    return EmbeddingProviderEntry(
        name=name,
        backend=backend,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        enabled=enabled,
        aliases=aliases,
    )


def _build_config(data: dict[str, Any], fallback_default_provider: str) -> EmbeddingProvidersConfig:
    raw_providers = data.get("models")
    if not isinstance(raw_providers, dict) or not raw_providers:
        raw_providers = data.get("providers")
    if not isinstance(raw_providers, dict) or not raw_providers:
        raw_providers = _DEFAULT_CONFIG["models"]

    providers: dict[str, EmbeddingProviderEntry] = {}
    alias_map: dict[str, str] = {}
    for raw_name, raw_provider in raw_providers.items():
        name = _normalize_str(raw_name)
        if not name:
            continue

        entry = _parse_provider(name, raw_provider)
        providers[name] = entry
        for alias in entry.aliases:
            alias_map[alias] = name

        if entry.backend and entry.backend not in alias_map:
            alias_map[entry.backend] = name

    default_provider = _normalize_str(data.get("default_provider") or fallback_default_provider)
    if default_provider in alias_map:
        default_provider = alias_map[default_provider]

    if default_provider not in providers:
        enabled_candidates = [name for name, entry in providers.items() if entry.enabled]
        if enabled_candidates:
            default_provider = enabled_candidates[0]
        elif providers:
            default_provider = next(iter(providers))
        else:
            default_provider = _normalize_str(fallback_default_provider) or "openai_default"

    return EmbeddingProvidersConfig(
        default_provider=default_provider,
        providers=providers,
        alias_map=alias_map,
    )


@lru_cache(maxsize=4)
def load_embedding_providers_config(
    config_path: str = "src/app/config/embeddings.json",
    fallback_default_provider: str = "openai_default",
) -> EmbeddingProvidersConfig:
    path = Path(config_path)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path

    data: dict[str, Any] = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (json.JSONDecodeError, OSError):
            data = {}

    if not data:
        data = _DEFAULT_CONFIG

    return _build_config(data, fallback_default_provider=fallback_default_provider)