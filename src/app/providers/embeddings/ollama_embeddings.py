from __future__ import annotations

import httpx

from app.contracts.providers import BaseEmbeddingProvider, EmbeddingRequest, EmbeddingResponse
from app.config.settings import Settings


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    name = "ollama"

    def __init__(self, settings: Settings, base_url: str | None = None) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url or settings.ollama_base_url,
            timeout=120.0,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        model = request.model or "nomic-embed-text"
        vectors: list[list[float]] = []
        for text in request.texts:
            response = await self._client.post(
                "/api/embeddings",
                json={"model": model, "prompt": text},
            )
            response.raise_for_status()
            vectors.append(response.json().get("embedding", []))
        return EmbeddingResponse(vectors=vectors, model=model)
