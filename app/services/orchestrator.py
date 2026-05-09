from __future__ import annotations

from app.domain.models import AIInvokeRequest, AIInvokeResponse, new_trace_id
from app.graphs.builder import AIGraphRunner


class AIOrchestrator:
    def __init__(self, graph_runner: AIGraphRunner) -> None:
        self.graph_runner = graph_runner

    async def invoke(self, request: AIInvokeRequest) -> AIInvokeResponse:
        trace_id = new_trace_id()
        return await self.graph_runner.run(request, trace_id)
