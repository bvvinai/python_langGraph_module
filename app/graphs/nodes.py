from __future__ import annotations

from app.domain.models import AIInvokeResponse
from app.graphs.state import AIState
from app.domain.ports import VectorStore
from app.providers.factory import ProviderFactory


class AINodes:
    def __init__(self, provider_factory: ProviderFactory, vector_store: VectorStore, default_collection: str) -> None:
        self.provider_factory = provider_factory
        self.vector_store = vector_store
        self.default_collection = default_collection

    async def prepare(self, state: AIState) -> AIState:
        request = state["request"]
        selected_provider = request.provider or self.provider_factory.default_provider
        return {"provider_name": selected_provider, "model_input": request.input, "retrieved_context": []}

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

        context_lines = [f"[{idx}] {chunk.text}" for idx, chunk in enumerate(chunks, start=1)]
        context_block = "\n".join(context_lines)
        model_input = (
            "Use the following retrieved context to answer the user request. "
            "If context is insufficient, say so clearly.\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            f"User request:\n{request.input}"
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
