from __future__ import annotations

from typing import Any

from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from app.contracts.providers import BaseVectorStore
from app.config.settings import Settings
from app.utils.id_normalizers import stable_uuid


class QdrantVectorStore(BaseVectorStore):
    name = "qdrant"

    def __init__(self, settings: Settings) -> None:
        self._client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    async def upsert(
        self,
        collection: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        points = [
            qm.PointStruct(id=stable_uuid(point_id), vector=vector, payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads, strict=True)
        ]
        await self._client.upsert(collection_name=collection, points=points, wait=True)

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query_filter = None
        if filters:
            must_filters = [
                qm.FieldCondition(key=key, match=qm.MatchValue(value=value))
                for key, value in filters.items()
            ]
            query_filter = qm.Filter(must=must_filters)

        results = await self._client.search(
            collection_name=collection,
            query_vector=vector,
            limit=limit,
            query_filter=query_filter,
        )
        return [
            {
                "id": str(row.id),
                "score": row.score,
                "payload": row.payload,
            }
            for row in results
        ]
