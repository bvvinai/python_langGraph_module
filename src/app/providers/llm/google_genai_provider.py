from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from google import genai

from app.contracts.providers import BaseLLMProvider, LLMMessage, LLMRequest, LLMResponse
from app.config.settings import Settings
from app.core.exceptions import ProviderConfigurationError


def _messages_to_prompt(messages: list[LLMMessage]) -> str:
    lines: list[str] = []
    for message in messages:
        role = (message.role or "user").strip().lower()
        content = (message.content or "").strip()
        if not content:
            continue
        lines.append(f"{role}: {content}")
    return "\n".join(lines).strip()


class GoogleGenAIProvider(BaseLLMProvider):
    name = "google_genai"

    def __init__(self, settings: Settings, api_key: str | None = None) -> None:
        resolved_api_key = api_key or settings.google_genai_api_key
        if not resolved_api_key:
            raise ProviderConfigurationError(self.name, "GOOGLE_GENAI_API_KEY is missing")
        self._settings = settings
        self._client = genai.Client(api_key=resolved_api_key)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or "gemini-1.5-flash"
        prompt = _messages_to_prompt(request.messages)
        if not prompt:
            prompt = "user:"

        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=model,
            contents=prompt,
        )

        text = getattr(response, "text", "") or ""
        usage_raw = getattr(response, "usage_metadata", None)
        usage = usage_raw.model_dump() if hasattr(usage_raw, "model_dump") else None
        if usage is None and isinstance(usage_raw, dict):
            usage = usage_raw
        return LLMResponse(text=text, model=model, usage=usage)

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        result = await self.generate(request)
        if result.text:
            yield result.text
