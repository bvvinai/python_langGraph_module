from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.domain.ports import RetrievedChunk, VectorDocument


class RetrievalConfig(BaseModel):
    enabled: bool = False
    collection: str | None = None
    top_k: int = Field(default=4, ge=1, le=20)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


class AIInvokeRequest(BaseModel):
    input: str = Field(min_length=1, description="Primary user input")
    system_prompt: str | None = Field(default=None)
    provider: str | None = Field(default=None)
    model: str | None = Field(default=None)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    retrieval: RetrievalConfig | None = None
    rag_mode: str | None = Field(default=None, description="rag or graph_rag")


class AIInvokeResponse(BaseModel):
    output: str
    provider: str
    model: str | None = None
    trace_id: str
    raw: dict[str, Any] | None = None
    retrieved_context: list[RetrievedChunk] = Field(default_factory=list)


class VectorUpsertRequest(BaseModel):
    collection: str | None = None
    documents: list[VectorDocument] = Field(default_factory=list)


class VectorUpsertResponse(BaseModel):
    collection: str
    upserted: int


class VectorRuntimeConfigResponse(BaseModel):
    rag_mode: str
    vector_db_enabled: bool
    vector_db_provider: str
    vector_db_default_collection: str
    qdrant_url: str
    graph_db_enabled: bool
    graph_db_provider: str
    neo4j_uri: str
    embeddings_config_path: str
    embedding_profile: str
    available_embedding_profiles: list[str]


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str


class ProviderInfo(BaseModel):
    name: str


class ProviderListResponse(BaseModel):
    default_provider: str
    providers: list[ProviderInfo]


def new_trace_id() -> str:
    return str(uuid4())
