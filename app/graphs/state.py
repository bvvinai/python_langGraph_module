from __future__ import annotations

from typing import TypedDict

from app.domain.models import AIInvokeRequest, AIInvokeResponse
from app.domain.ports import ProviderOutput, RetrievedChunk


class AIState(TypedDict, total=False):
    request: AIInvokeRequest
    trace_id: str
    provider_name: str
    model_input: str
    retrieved_context: list[RetrievedChunk]
    provider_output: ProviderOutput
    response: AIInvokeResponse
