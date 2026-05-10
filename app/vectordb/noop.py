from __future__ import annotations

from app.domain.ports import RetrievedChunk, VectorDocument, VectorStore


class NoopVectorStore(VectorStore):
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
        return []
