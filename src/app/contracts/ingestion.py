from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class DocumentBlob:
    document_id: str
    filename: str
    content_type: str
    content_bytes: bytes
    source: str = "upload"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    index: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IngestionJob:
    job_id: str
    document_id: str
    status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message: str = ""
    stats: dict[str, Any] = field(default_factory=dict)


class BaseLoader(ABC):
    name: str

    @abstractmethod
    def supports(self, filename: str, content_type: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def load(self, blob: DocumentBlob) -> ParsedDocument:
        raise NotImplementedError


class BaseChunker(ABC):
    name: str

    @abstractmethod
    def chunk(self, parsed: ParsedDocument, chunk_size: int, overlap: int) -> list[Chunk]:
        raise NotImplementedError
