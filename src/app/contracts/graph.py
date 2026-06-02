from __future__ import annotations

from typing import TypedDict


class GraphRequest(TypedDict, total=False):
    query: str
    mode: str
    provider: str
    model: str
    vector_enabled: bool
    graph_enabled: bool
    metadata: dict[str, object]


class GraphState(TypedDict, total=False):
    input: GraphRequest
    response_text: str
    retrieved_context: list[dict[str, object]]
    graph_context: list[dict[str, object]]
    errors: list[str]
