from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.config.settings import Settings, get_settings
from app.graph.runtime import GraphRuntime
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.versioning.store import VersionStore
from app.router.embedding_router import EmbeddingRouter
from app.router.model_router import ModelRouter
from app.services.provider_manager import ProviderManager


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    providers: ProviderManager
    model_router: ModelRouter
    embedding_router: EmbeddingRouter
    graph_runtime: GraphRuntime
    version_store: VersionStore
    ingestion_pipeline: IngestionPipeline


@lru_cache(maxsize=1)
def get_container() -> AppContainer:
    settings = get_settings()
    providers = ProviderManager(settings)
    model_router = ModelRouter(settings)
    embedding_router = EmbeddingRouter(settings)

    graph_runtime = GraphRuntime(
        providers=providers,
        model_router=model_router,
        embedding_router=embedding_router,
    )
    version_store = VersionStore()
    ingestion_pipeline = IngestionPipeline(
        settings=settings,
        providers=providers,
        embedding_router=embedding_router,
        version_store=version_store,
    )

    return AppContainer(
        settings=settings,
        providers=providers,
        model_router=model_router,
        embedding_router=embedding_router,
        graph_runtime=graph_runtime,
        version_store=version_store,
        ingestion_pipeline=ingestion_pipeline,
    )
