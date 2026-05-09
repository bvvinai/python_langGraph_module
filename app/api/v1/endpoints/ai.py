from __future__ import annotations

from fastapi import APIRouter, Depends

from app.domain.models import AIInvokeRequest, AIInvokeResponse
from app.services.orchestrator import AIOrchestrator
from app.services.runtime import get_orchestrator

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/invoke", response_model=AIInvokeResponse)
async def invoke_ai(
    request: AIInvokeRequest,
    orchestrator: AIOrchestrator = Depends(get_orchestrator),
) -> AIInvokeResponse:
    return await orchestrator.invoke(request)
