from __future__ import annotations

from app.core.exceptions import ProviderNotFoundError
from app.domain.ports import LLMProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.openai_compatible import OpenAICompatibleProvider
from app.providers.ollama import OllamaProvider
from app.providers.registry import ProviderConfig, ProviderRegistry


class ProviderFactory:
    def __init__(self, registry: ProviderRegistry, default_provider: str) -> None:
        self._registry = {item.name: item for item in registry.providers if item.enabled}
        self.default_provider = default_provider
        if self.default_provider not in self._registry and self._registry:
            self.default_provider = sorted(self._registry.keys())[0]
        self._instances: dict[str, LLMProvider] = {}

    def list_providers(self) -> list[str]:
        return sorted(self._registry.keys())

    def get(self, name: str | None = None) -> LLMProvider:
        selected = name or self.default_provider
        if selected not in self._registry:
            raise ProviderNotFoundError(selected)

        if selected not in self._instances:
            self._instances[selected] = self._build(self._registry[selected])
        return self._instances[selected]

    @staticmethod
    def _build(config: ProviderConfig) -> LLMProvider:
        if config.type == "anthropic":
            return AnthropicProvider(config)
        if config.type == "openai_compatible":
            return OpenAICompatibleProvider(config)
        if config.type == "ollama":
            return OllamaProvider(config)
        raise ProviderNotFoundError(config.name)
