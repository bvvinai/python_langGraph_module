from __future__ import annotations

from uuid import uuid4

import httpx

from app.domain.ports import RetrievedChunk, VectorDocument, VectorStore
from app.vectordb.embedding import EmbeddingModel


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None,
        timeout_seconds: float,
        distance: str,
        embedding_model: EmbeddingModel,
    ) -> None:
        normalized_base_url = base_url.strip()
        if not normalized_base_url:
            normalized_base_url = "http://localhost:6333"
        if not normalized_base_url.startswith(("http://", "https://")):
            normalized_base_url = f"http://{normalized_base_url}"

        if normalized_base_url in {"http://", "https://"}:
            normalized_base_url = "http://localhost:6333"

        self.base_url = normalized_base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds)
        self.distance = distance
        self.embedding_model = embedding_model
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["api-key"] = api_key

    async def _ensure_collection(self, collection: str, *, vector_size: int) -> None:
        url = f"{self.base_url}/collections/{collection}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self.headers)
            if response.status_code == 200:
                return

            payload = {
                "vectors": {
                    "size": vector_size,
                    "distance": self.distance,
                }
            }
            await client.put(url, headers=self.headers, json=payload)

    async def upsert_documents(
        self,
        *,
        collection: str,
        documents: list[VectorDocument],
    ) -> int:
        if not documents:
            return 0

        points = []
        for item in documents:
            point_id = item.id or str(uuid4())
            vector = await self.embedding_model.embed(item.text)
            payload = {
                "text": item.text,
                "metadata": item.metadata,
            }
            points.append({"id": point_id, "vector": vector, "payload": payload})

        if not points or not points[0]["vector"]:
            return 0

        first_vector = points[0]["vector"]
        vector_size = len(first_vector) if isinstance(first_vector, list) else 0
        if vector_size <= 0:
            return 0

        await self._ensure_collection(collection, vector_size=vector_size)

        url = f"{self.base_url}/collections/{collection}/points?wait=true"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            await client.put(url, headers=self.headers, json={"points": points})

        return len(points)

    async def search(
        self,
        *,
        collection: str,
        query: str,
        limit: int,
        score_threshold: float | None,
    ) -> list[RetrievedChunk]:
        if limit <= 0:
            return []

        vector = await self.embedding_model.embed(query)
        if not vector:
            return []

        await self._ensure_collection(collection, vector_size=len(vector))
        body: dict[str, object] = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
        }
        if score_threshold is not None:
            body["score_threshold"] = score_threshold

        url = f"{self.base_url}/collections/{collection}/points/search"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=self.headers, json=body)

        if response.status_code >= 400:
            return []

        payload = response.json()
        result = payload.get("result", [])
        chunks: list[RetrievedChunk] = []
        for item in result:
            point_payload = item.get("payload", {})
            metadata = point_payload.get("metadata", {})
            chunks.append(
                RetrievedChunk(
                    id=str(item.get("id", "")),
                    text=str(point_payload.get("text", "")),
                    score=float(item.get("score", 0.0)),
                    metadata=metadata if isinstance(metadata, dict) else {},
                )
            )

        return chunks
