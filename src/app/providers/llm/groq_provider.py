from __future__ import annotations

from collections.abc import AsyncGenerator

from groq import AsyncGroq

from app.contracts.providers import BaseLLMProvider, LLMRequest, LLMResponse
from app.config.settings import Settings
from app.core.exceptions import ProviderConfigurationError


class GroqProvider(BaseLLMProvider):
    name = "groq"

    def __init__(self, settings: Settings, api_key: str | None = None) -> None:
        resolved_api_key = api_key or settings.groq_api_key
        if not resolved_api_key:
            raise ProviderConfigurationError(self.name, "GROQ_API_KEY is missing")
        self._settings = settings
        self._client = AsyncGroq(api_key=resolved_api_key)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or "llama-3.1-8b-instant"
        response = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
        )

        text = response.choices[0].message.content or ""
        usage = response.usage.model_dump() if response.usage else None
        return LLMResponse(text=text, model=model, usage=usage)

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        model = request.model or "llama-3.1-8b-instant"
        stream = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )

        async for event in stream:
            if not event.choices:
                continue
            delta = event.choices[0].delta.content
            if delta:
                yield delta
