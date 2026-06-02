from __future__ import annotations

from openai import AsyncOpenAI

from app.contracts.providers import BaseEmbeddingProvider, EmbeddingRequest, EmbeddingResponse
from app.config.settings import Settings
from app.core.exceptions import ProviderConfigurationError


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    name = "openai"

    def __init__(
        self,
        settings: Settings,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        resolved_api_key = api_key or settings.openai_api_key
        if not resolved_api_key:
            raise ProviderConfigurationError(self.name, "OPENAI_API_KEY is missing")
        self._settings = settings
        client_kwargs: dict[str, str] = {"api_key": resolved_api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**client_kwargs)

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        model = request.model or self._settings.default_embedding_model
        response = await self._client.embeddings.create(model=model, input=request.texts)
        vectors = [item.embedding for item in response.data]
        return EmbeddingResponse(vectors=vectors, model=model)
