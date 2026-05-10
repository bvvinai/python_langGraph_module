from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.domain.models import AIInvokeRequest, RetrievalConfig
from app.domain.ports import ProviderOutput, RetrievedChunk, VectorDocument, VectorStore
from app.graphs.builder import AIGraphRunner
from app.main import create_app
from app.services.runtime import get_vector_store


class FakeProvider:
    name = "fake"

    async def generate(
        self,
        *,
        user_input: str,
        system_prompt: str | None,
        model: str | None,
        temperature: float,
        max_tokens: int | None,
        metadata: dict[str, Any],
    ) -> ProviderOutput:
        return ProviderOutput(text=user_input, model="fake-model", raw={})


class FakeProviderFactory:
    def __init__(self) -> None:
        self.default_provider = "fake"

    def get(self, name: str | None = None) -> FakeProvider:
        return FakeProvider()


class FakeVectorStore(VectorStore):
    async def upsert_documents(
        self,
        *,
        collection: str,
        documents: list[VectorDocument],
    ) -> int:
        return len(documents)

    async def search(
        self,
        *,
        collection: str,
        query: str,
        limit: int,
        score_threshold: float | None,
    ) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                id="chunk-1",
                text="LangGraph coordinates stateful workflows.",
                score=0.9,
                metadata={"source": "kb"},
            )
        ]


@pytest.mark.asyncio
async def test_graph_runner_uses_retrieval_context() -> None:
    runner = AIGraphRunner(
        provider_factory=FakeProviderFactory(),
        vector_store=FakeVectorStore(),
        default_collection="knowledge_base",
    )
    request = AIInvokeRequest(
        input="What is LangGraph?",
        retrieval=RetrievalConfig(enabled=True, top_k=1),
    )

    response = await runner.run(request=request, trace_id="trace-test")

    assert "Retrieved context:" in response.output
    assert response.provider == "fake"
    assert len(response.retrieved_context) == 1


def test_vector_upsert_endpoint() -> None:
    app = create_app()
    app.dependency_overrides[get_vector_store] = lambda: FakeVectorStore()
    client = TestClient(app)

    response = client.post(
        "/v1/ai/vector/upsert",
        json={
            "collection": "knowledge_base",
            "documents": [
                {"id": "doc-1", "text": "LangGraph is a framework.", "metadata": {"topic": "graph"}}
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["collection"] == "knowledge_base"
    assert body["upserted"] == 1


def test_vector_runtime_config_endpoint() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/v1/ai/vector/config")

    assert response.status_code == 200
    body = response.json()
    assert "vector_db_enabled" in body
    assert "vector_db_provider" in body
    assert "embedding_profile" in body
    assert "available_embedding_profiles" in body
    assert "embedding_provider" in body
    assert "embedding_model" in body
