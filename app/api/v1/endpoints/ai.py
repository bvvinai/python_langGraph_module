from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.domain.models import (
    AIInvokeRequest,
    AIInvokeResponse,
    ProviderInfo,
    ProviderListResponse,
    VectorRuntimeConfigResponse,
    VectorUpsertRequest,
    VectorUpsertResponse,
)
from app.domain.ports import VectorStore
from app.providers.factory import ProviderFactory
from app.services.orchestrator import AIOrchestrator
from app.services.runtime import get_orchestrator, get_provider_factory, get_vector_store
from app.vectordb.registry import load_embedding_registry

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers(
    provider_factory: ProviderFactory = Depends(get_provider_factory),
) -> ProviderListResponse:
    return ProviderListResponse(
        default_provider=provider_factory.default_provider,
        providers=[ProviderInfo(name=name) for name in provider_factory.list_providers()],
    )


@router.post("/invoke", response_model=AIInvokeResponse)
async def invoke_ai(
    request: AIInvokeRequest,
    orchestrator: AIOrchestrator = Depends(get_orchestrator),
) -> AIInvokeResponse:
    return await orchestrator.invoke(request)


@router.post("/vector/upsert", response_model=VectorUpsertResponse)
async def upsert_vector_documents(
    request: VectorUpsertRequest,
    vector_store: VectorStore = Depends(get_vector_store),
) -> VectorUpsertResponse:
    settings = get_settings()
    collection = request.collection or settings.vector_db_default_collection
    upserted = await vector_store.upsert_documents(collection=collection, documents=request.documents)
    return VectorUpsertResponse(collection=collection, upserted=upserted)


@router.get("/vector/config", response_model=VectorRuntimeConfigResponse)
async def get_vector_runtime_config() -> VectorRuntimeConfigResponse:
    settings = get_settings()
    registry = load_embedding_registry(settings.embeddings_config_path)
    enabled_profiles = [item for item in registry.embeddings if item.enabled]
    available_profiles = [item.name for item in enabled_profiles]
    selected = next((item for item in enabled_profiles if item.name == settings.embedding_profile), None)

    return VectorRuntimeConfigResponse(
        vector_db_enabled=settings.vector_db_enabled,
        vector_db_provider=settings.vector_db_provider,
        vector_db_default_collection=settings.vector_db_default_collection,
        qdrant_url=settings.qdrant_url,
        embeddings_config_path=settings.embeddings_config_path,
        embedding_profile=settings.embedding_profile,
        available_embedding_profiles=available_profiles,
        embedding_provider=(selected.type if selected else settings.embedding_provider),
        embedding_model=(selected.model if selected and selected.model else settings.embedding_model),
        embedding_base_url=(selected.base_url if selected and selected.base_url else settings.embedding_base_url),
        embedding_endpoint_path=(
            selected.endpoint_path
            if selected and selected.endpoint_path
            else settings.embedding_endpoint_path
        ),
    )
