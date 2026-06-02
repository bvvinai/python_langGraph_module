from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

NodeFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class NodeRegistry:
    def __init__(self) -> None:
        self._nodes: dict[str, NodeFn] = {}

    def register(self, name: str, node: NodeFn) -> None:
        self._nodes[name] = node

    def get(self, name: str) -> NodeFn:
        return self._nodes[name]

    def available(self) -> list[str]:
        return sorted(self._nodes)
