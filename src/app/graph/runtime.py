from __future__ import annotations

from typing import Any

from app.contracts.graph import GraphRequest, GraphState
from app.contracts.providers import EmbeddingRequest, LLMMessage, LLMRequest
from app.router.embedding_router import EmbeddingRouter
from app.router.model_router import ModelRouter
from app.services.provider_manager import ProviderManager

from .graph_builder import build_graph


class GraphRuntime:
    def __init__(
        self,
        providers: ProviderManager,
        model_router: ModelRouter,
        embedding_router: EmbeddingRouter,
    ) -> None:
        self._providers = providers
        self._model_router = model_router
        self._embedding_router = embedding_router
        self._graph = build_graph(self._llm_node, self._retrieve_node, self._graph_node)

    @staticmethod
    def _request_metadata(request: GraphRequest) -> dict[str, Any]:
        metadata_raw = request.get("metadata")
        return metadata_raw if isinstance(metadata_raw, dict) else {}

    def _resolve_llm_provider(self, request: GraphRequest) -> str:
        return self._model_router.route(request.get("provider"))

    async def invoke(self, request: GraphRequest) -> dict[str, Any]:
        initial: GraphState = {
            "input": request,
            "retrieved_context": [],
            "graph_context": [],
            "errors": [],
        }
        result = await self._graph.ainvoke(initial)
        return {
            "text": result.get("response_text", ""),
            "retrieved_context": result.get("retrieved_context", []),
            "graph_context": result.get("graph_context", []),
            "errors": result.get("errors", []),
        }

    async def stream(self, request: GraphRequest):
        provider_name = self._resolve_llm_provider(request)
        llm = self._providers.get_llm(provider_name)
        llm_request = LLMRequest(
            messages=[LLMMessage(role="user", content=request.get("query", ""))],
            model=request.get("model"),
        )
        async for token in llm.stream_generate(llm_request):
            yield token

    async def _retrieve_node(self, state: GraphState) -> GraphState:
        request = state.get("input", {})
        if not request.get("vector_enabled", True):
            return {"retrieved_context": []}

        try:
            provider = self._embedding_router.route(requested_provider=None)
            embedder = self._providers.get_embedding(provider)
            query = request.get("query", "")
            embedding = await embedder.embed(EmbeddingRequest(texts=[query], model=None))

            vector_store = self._providers.get_vector_store()
            metadata = self._request_metadata(request)
            hits = await vector_store.search(
                collection=metadata.get("collection", self._providers.default_vector_collection),
                vector=embedding.vectors[0],
                limit=5,
            )
            return {"retrieved_context": hits}
        except Exception as exc:  # noqa: BLE001
            errors = list(state.get("errors", []))
            errors.append(f"retrieve_node: {exc}")
            return {"retrieved_context": [], "errors": errors}

    async def _graph_node(self, state: GraphState) -> GraphState:
        request = state.get("input", {})
        if not request.get("graph_enabled", True):
            return {"graph_context": []}

        try:
            graph_store = self._providers.get_graph_store("neo4j")
            metadata = self._request_metadata(request)
            rows = await graph_store.query(
                "MATCH (d:Document)-[:HAS_ENTITY]->(e:Entity) WHERE d.id = $doc_id RETURN e LIMIT 10",
                {"doc_id": metadata.get("document_id", "")},
            )
            return {"graph_context": rows}
        except Exception as exc:  # noqa: BLE001
            errors = list(state.get("errors", []))
            errors.append(f"graph_node: {exc}")
            return {"graph_context": [], "errors": errors}

    async def _llm_node(self, state: GraphState) -> GraphState:
        request = state.get("input", {})
        provider_name = self._resolve_llm_provider(request)
        llm = self._providers.get_llm(provider_name)

        context_parts: list[str] = []
        if request.get("mode") in {"rag", "graph_rag"}:
            retrieved = state.get("retrieved_context", [])
            if retrieved:
                context_parts.append("Retrieved context:\n" + "\n".join(str(item) for item in retrieved[:5]))
        if request.get("mode") == "graph_rag":
            graph_rows = state.get("graph_context", [])
            if graph_rows:
                context_parts.append("Graph context:\n" + "\n".join(str(item) for item in graph_rows[:5]))

        prompt = request.get("query", "")
        if context_parts:
            prompt = f"{'\n\n'.join(context_parts)}\n\nUser query:\n{prompt}"

        response = await llm.generate(
            LLMRequest(
                messages=[LLMMessage(role="user", content=prompt)],
                model=request.get("model"),
                temperature=0.2,
                max_tokens=1024,
                metadata=request.get("metadata"),
            )
        )
        return {"response_text": response.text}
