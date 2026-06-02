from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseSourceConnector(ABC):
    name: str

    @abstractmethod
    async def healthcheck(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def fetch(self, source: str, options: dict[str, Any] | None = None) -> bytes:
        raise NotImplementedError
