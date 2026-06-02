from __future__ import annotations

from app.config.settings import Settings
from app.core.llm_provider_config import LLMProvidersConfig, load_llm_providers_config


class ModelRouter:
    def __init__(self, settings: Settings) -> None:
        self._llm_config: LLMProvidersConfig = load_llm_providers_config(
            config_path=settings.llm_provider_config_path,
            fallback_default_provider="openai_default",
        )

    def _is_provider_enabled(self, provider: str | None) -> bool:
        if not provider:
            return False

        return self._llm_config.provider_enabled(provider)

    def route(self, requested_provider: str | None = None) -> str:
        if requested_provider:
            resolved = self._llm_config.resolve_provider(requested_provider)
            return resolved or requested_provider

        if self._is_provider_enabled(self._llm_config.default_provider):
            return self._llm_config.default_provider

        for model_key, model_entry in self._llm_config.providers.items():
            if model_entry.enabled:
                return model_key

        return self._llm_config.default_provider
