from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.domain.ports import GraphStore
from app.graphs.builder import AIGraphRunner
from app.domain.ports import VectorStore
from app.graphdb.factory import build_graph_store
from app.providers.factory import ProviderFactory
from app.providers.registry import load_provider_registry
from app.services.orchestrator import AIOrchestrator
from app.vectordb.factory import build_vector_store


@lru_cache(maxsize=1)
def get_provider_factory() -> ProviderFactory:
    settings = get_settings()
    registry = load_provider_registry(settings.providers_config_path)
    return ProviderFactory(registry=registry, default_provider=settings.default_provider)


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return build_vector_store(settings)


@lru_cache(maxsize=1)
def get_graph_store() -> GraphStore | None:
    settings = get_settings()
    return build_graph_store(settings)


@lru_cache(maxsize=1)
def get_orchestrator() -> AIOrchestrator:
    settings = get_settings()
    provider_factory = get_provider_factory()
    vector_store = get_vector_store()
    graph_store = get_graph_store()
    graph_runner = AIGraphRunner(
        provider_factory=provider_factory,
        vector_store=vector_store,
        default_collection=settings.vector_db_default_collection,
        default_rag_mode=settings.rag_mode,
        graph_store=graph_store,
    )
    return AIOrchestrator(graph_runner=graph_runner)
