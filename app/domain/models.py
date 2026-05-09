from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AIInvokeRequest(BaseModel):
    input: str = Field(min_length=1, description="Primary user input")
    system_prompt: str | None = Field(default=None)
    provider: str | None = Field(default=None)
    model: str | None = Field(default=None)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIInvokeResponse(BaseModel):
    output: str
    provider: str
    model: str | None = None
    trace_id: str
    raw: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str


def new_trace_id() -> str:
    return str(uuid4())
