from __future__ import annotations

from fastapi import APIRouter, Depends

from app.domain.models import AIInvokeRequest, AIInvokeResponse, ProviderInfo, ProviderListResponse
from app.providers.factory import ProviderFactory
from app.services.orchestrator import AIOrchestrator
from app.services.runtime import get_orchestrator, get_provider_factory

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
