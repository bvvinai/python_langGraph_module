from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class InvokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    mode: Literal["agent", "rag", "graph_rag"] = "agent"
    provider: str | None = None
    model: str | None = None
    vector_enabled: bool = True
    graph_enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class InvokeResponse(BaseModel):
    text: str
    retrieved_context: list[dict[str, Any]] = Field(default_factory=list)
    graph_context: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class IngestionJobResponse(BaseModel):
    job_id: str
    document_id: str
    status: str
    message: str
    stats: dict[str, Any] = Field(default_factory=dict)
