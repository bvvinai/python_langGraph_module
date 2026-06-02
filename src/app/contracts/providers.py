from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LLMMessage:
    role: str
    content: str


@dataclass(slots=True)
class LLMRequest:
    messages: list[LLMMessage]
    model: str | None = None
    temperature: float = 0.2
    max_tokens: int | None = None
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class LLMResponse:
    text: str
    model: str
    usage: dict[str, Any] | None = None


@dataclass(slots=True)
class EmbeddingRequest:
    texts: list[str]
    model: str | None = None


@dataclass(slots=True)
class EmbeddingResponse:
    vectors: list[list[float]]
    model: str


class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream_generate(self, request: LLMRequest):
        raise NotImplementedError


class BaseEmbeddingProvider(ABC):
    name: str

    @abstractmethod
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise NotImplementedError


class BaseVectorStore(ABC):
    name: str

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class BaseGraphStore(ABC):
    name: str

    @abstractmethod
    async def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def upsert_entities(
        self,
        document_id: str,
        entities: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
    ) -> None:
        raise NotImplementedError
