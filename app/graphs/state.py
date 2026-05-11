from __future__ import annotations

from typing import TypedDict

from app.domain.models import AIInvokeRequest, AIInvokeResponse
from app.domain.ports import GraphNeighborhood, ProviderOutput, RetrievedChunk


class AIState(TypedDict, total=False):
    request: AIInvokeRequest
    trace_id: str
    provider_name: str
    rag_mode: str
    model_input: str
    retrieved_context: list[RetrievedChunk]
    graph_context: GraphNeighborhood
    graph_rag_fallback_used: bool
    provider_output: ProviderOutput
    response: AIInvokeResponse
