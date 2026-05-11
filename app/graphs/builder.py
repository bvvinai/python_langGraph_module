from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.domain.models import AIInvokeRequest, AIInvokeResponse
from app.domain.ports import GraphStore, VectorStore
from app.graphs.nodes import AINodes
from app.graphs.state import AIState
from app.providers.factory import ProviderFactory


class AIGraphRunner:
    def __init__(
        self,
        provider_factory: ProviderFactory,
        vector_store: VectorStore,
        default_collection: str,
        default_rag_mode: str,
        graph_store: GraphStore | None = None,
    ) -> None:
        self._nodes = AINodes(
            provider_factory=provider_factory,
            vector_store=vector_store,
            default_collection=default_collection,
            default_rag_mode=default_rag_mode,
            graph_store=graph_store,
        )

        workflow = StateGraph(AIState)
        workflow.add_node("prepare", self._nodes.prepare)
        workflow.add_node("retrieve_context", self._nodes.retrieve_context)
        workflow.add_node("call_model", self._nodes.call_model)
        workflow.add_node("finalize", self._nodes.finalize)

        workflow.set_entry_point("prepare")
        workflow.add_edge("prepare", "retrieve_context")
        workflow.add_edge("retrieve_context", "call_model")
        workflow.add_edge("call_model", "finalize")
        workflow.add_edge("finalize", END)

        self._graph = workflow.compile()

    async def run(self, request: AIInvokeRequest, trace_id: str) -> AIInvokeResponse:
        state = AIState(request=request, trace_id=trace_id)
        result = await self._graph.ainvoke(state)
        return result["response"]
