from __future__ import annotations

from app.config.settings import Settings
from app.core.embedding_provider_config import (
    EmbeddingProvidersConfig,
    load_embedding_providers_config,
)


class EmbeddingRouter:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._embedding_config: EmbeddingProvidersConfig = load_embedding_providers_config(
            config_path=settings.embedding_provider_config_path,
            fallback_default_provider=settings.default_embedding_provider,
        )

    def _backend_enabled(self, backend: str) -> bool:
        return {
            "openai": self._settings.enable_embedding_openai,
            "ollama": self._settings.enable_embedding_ollama,
        }.get(backend, True)

    def _is_provider_enabled(self, provider: str | None) -> bool:
        resolved = self._embedding_config.resolve_provider(provider)
        if not resolved:
            return False
        entry = self._embedding_config.provider_entry(resolved)
        return bool(entry and entry.enabled and self._backend_enabled(entry.backend))

    def route(self, collection: str | None = None, requested_provider: str | None = None) -> str:
        if requested_provider:
            resolved = self._embedding_config.resolve_provider(requested_provider)
            return resolved or requested_provider

        if collection and collection.startswith("local_"):
            local_provider = self._embedding_config.resolve_provider("ollama")
            if self._is_provider_enabled(local_provider):
                return local_provider

        if self._is_provider_enabled(self._embedding_config.default_provider):
            return self._embedding_config.default_provider

        for model_key, model_entry in self._embedding_config.providers.items():
            if model_entry.enabled and self._backend_enabled(model_entry.backend):
                return model_key

        return self._embedding_config.default_provider
