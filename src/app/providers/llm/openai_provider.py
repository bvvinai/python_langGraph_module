from __future__ import annotations

from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.contracts.providers import BaseLLMProvider, LLMRequest, LLMResponse
from app.config.settings import Settings
from app.core.exceptions import ProviderConfigurationError


class OpenAIProvider(BaseLLMProvider):
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
        client_kwargs = {"api_key": resolved_api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**client_kwargs)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self._settings.default_llm_model
        response = await self._client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
        )
        text = response.choices[0].message.content or ""
        usage = response.usage.model_dump() if response.usage else None
        return LLMResponse(text=text, model=response.model or model, usage=usage)

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        model = request.model or self._settings.default_llm_model
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
