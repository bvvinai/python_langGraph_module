from __future__ import annotations

from typing import TypedDict

from app.domain.models import AIInvokeRequest, AIInvokeResponse
from app.domain.ports import ProviderOutput


class AIState(TypedDict, total=False):
    request: AIInvokeRequest
    trace_id: str
    provider_name: str
    provider_output: ProviderOutput
    response: AIInvokeResponse
