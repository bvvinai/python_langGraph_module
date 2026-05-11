from __future__ import annotations

from app.core.exceptions import InvalidRagModeError
from app.domain.models import AIInvokeResponse
from app.domain.ports import GraphStore, RetrievedChunk, VectorStore
from app.graphs.state import AIState
from app.providers.factory import ProviderFactory


ALLOWED_RAG_MODES = {"rag", "graph_rag"}


class AINodes:
    def __init__(
        self,
        provider_factory: ProviderFactory,
        vector_store: VectorStore,
        default_collection: str,
        default_rag_mode: str,
        graph_store: GraphStore | None = None,
    ) -> None:
        self.provider_factory = provider_factory
        self.vector_store = vector_store
        self.default_collection = default_collection
        self.default_rag_mode = default_rag_mode
        self.graph_store = graph_store

    async def prepare(self, state: AIState) -> AIState:
        request = state["request"]
        selected_provider = request.provider or self.provider_factory.default_provider
        rag_mode = request.rag_mode or self.default_rag_mode
        if rag_mode not in ALLOWED_RAG_MODES:
            raise InvalidRagModeError(rag_mode)
        return {
            "provider_name": selected_provider,
            "rag_mode": rag_mode,
            "model_input": request.input,
            "retrieved_context": [],
            "graph_rag_fallback_used": False,
        }

    async def retrieve_context(self, state: AIState) -> AIState:
        request = state["request"]
        retrieval = request.retrieval
        if not retrieval or not retrieval.enabled:
            return {}

        collection = retrieval.collection or self.default_collection
        chunks = await self.vector_store.search(
            collection=collection,
            query=request.input,
            limit=retrieval.top_k,
            score_threshold=retrieval.score_threshold,
        )
        if not chunks:
            return {}

        if state.get("rag_mode") == "graph_rag":
            return await self._build_graph_rag_context(
                collection=collection,
                query=request.input,
                chunks=chunks,
            )

        return self._build_rag_context(chunks=chunks, query=request.input)

    async def _build_graph_rag_context(
        self,
        *,
        collection: str,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> AIState:
        rag_context = self._build_rag_context(chunks=chunks, query=query)

        if self.graph_store is None:
            rag_context["graph_rag_fallback_used"] = True
            return rag_context

        neighborhood = await self.graph_store.query_neighborhood(
            collection=collection,
            query=query,
            limit=max(1, len(chunks)),
        )
        if not neighborhood.facts and not neighborhood.edges:
            rag_context["graph_rag_fallback_used"] = True
            return rag_context

        retrieved_lines = [f"[{idx}] {chunk.text}" for idx, chunk in enumerate(chunks, start=1)]
        graph_lines = [f"- {fact}" for fact in neighborhood.facts]
        if not graph_lines:
            graph_lines = [f"- {edge.source} -[{edge.relation}]-> {edge.target}" for edge in neighborhood.edges]

        model_input = (
            "Use both retrieved context and graph context to answer the user request. "
            "If context is insufficient, say so clearly.\n\n"
            f"Retrieved context:\n{'\n'.join(retrieved_lines)}\n\n"
            f"Graph context:\n{'\n'.join(graph_lines)}\n\n"
            f"User request:\n{query}"
        )
        return {
            "retrieved_context": chunks,
            "graph_context": neighborhood,
            "model_input": model_input,
        }

    def _build_rag_context(self, *, chunks: list[RetrievedChunk], query: str) -> AIState:
        context_lines = [f"[{idx}] {chunk.text}" for idx, chunk in enumerate(chunks, start=1)]
        context_block = "\n".join(context_lines)
        model_input = (
            "Use the following retrieved context to answer the user request. "
            "If context is insufficient, say so clearly.\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            f"User request:\n{query}"
        )
        return {"retrieved_context": chunks, "model_input": model_input}

    async def call_model(self, state: AIState) -> AIState:
        request = state["request"]
        provider = self.provider_factory.get(state["provider_name"])
        output = await provider.generate(
            user_input=state.get("model_input", request.input),
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )
        return {"provider_output": output}

    async def finalize(self, state: AIState) -> AIState:
        output = state["provider_output"]
        response = AIInvokeResponse(
            output=output.text,
            provider=state["provider_name"],
            model=output.model,
            trace_id=state["trace_id"],
            raw=output.raw,
            retrieved_context=state.get("retrieved_context", []),
        )
        return {"response": response}
