from __future__ import annotations

import asyncio
from typing import Any

import chromadb

from app.contracts.providers import BaseVectorStore
from app.config.settings import Settings


class ChromaVectorStore(BaseVectorStore):
    name = "chroma"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if settings.chroma_host:
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                ssl=settings.chroma_ssl,
            )
        else:
            self._client = chromadb.PersistentClient(path=settings.chroma_persist_directory)

        self._collection_metadata = {"hnsw:space": settings.chroma_distance_metric}

    def _collection(self, name: str):
        return self._client.get_or_create_collection(
            name=name,
            metadata=self._collection_metadata,
        )

    async def upsert(
        self,
        collection: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        def _run() -> None:
            col = self._collection(collection)
            metadatas = [payload if payload else {} for payload in payloads]
            col.upsert(ids=ids, embeddings=vectors, metadatas=metadatas)

        await asyncio.to_thread(_run)

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            col = self._collection(collection)
            result = col.query(
                query_embeddings=[vector],
                n_results=max(1, limit),
                where=filters or None,
            )

            ids = (result.get("ids") or [[]])[0]
            distances = (result.get("distances") or [[]])[0]
            metadatas = (result.get("metadatas") or [[]])[0]

            rows: list[dict[str, Any]] = []
            for index, item_id in enumerate(ids):
                distance = distances[index] if index < len(distances) else None
                metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
                score = None
                if isinstance(distance, (int, float)):
                    score = 1.0 - float(distance)

                rows.append(
                    {
                        "id": str(item_id),
                        "score": score,
                        "distance": distance,
                        "payload": metadata,
                    }
                )
            return rows

        return await asyncio.to_thread(_run)
