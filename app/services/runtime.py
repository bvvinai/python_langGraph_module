from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.graphs.builder import AIGraphRunner
from app.providers.factory import ProviderFactory
from app.providers.registry import load_provider_registry
from app.services.orchestrator import AIOrchestrator


@lru_cache(maxsize=1)
def get_orchestrator() -> AIOrchestrator:
    settings = get_settings()
    registry = load_provider_registry(settings.providers_config_path)
    provider_factory = ProviderFactory(registry=registry, default_provider=settings.default_provider)
    graph_runner = AIGraphRunner(provider_factory=provider_factory)
    return AIOrchestrator(graph_runner=graph_runner)
