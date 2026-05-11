from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ProviderOutput(BaseModel):
    text: str
    model: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class VectorDocument(BaseModel):
    id: str | None = None
    text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    relation: str
    target: str
    weight: float = 1.0


class GraphNeighborhood(BaseModel):
    entities: list[str] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    async def generate(
        self,
        *,
        user_input: str,
        system_prompt: str | None,
        model: str | None,
        temperature: float,
        max_tokens: int | None,
        metadata: dict[str, Any],
    ) -> ProviderOutput: ...


@runtime_checkable
class VectorStore(Protocol):
    async def upsert_documents(
        self,
        *,
        collection: str,
        documents: list[VectorDocument],
    ) -> int: ...

    async def search(
        self,
        *,
        collection: str,
        query: str,
        limit: int,
        score_threshold: float | None,
    ) -> list[RetrievedChunk]: ...


@runtime_checkable
class GraphStore(Protocol):
    async def upsert_documents(
        self,
        *,
        collection: str,
        documents: list[VectorDocument],
    ) -> int: ...

    async def query_neighborhood(
        self,
        *,
        collection: str,
        query: str,
        limit: int,
    ) -> GraphNeighborhood: ...
