from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

try:
    from mistralai import Mistral
except ImportError:  # mistralai>=2.x exposes the client from mistralai.client
    from mistralai.client import Mistral

from app.contracts.providers import BaseLLMProvider, LLMRequest, LLMResponse
from app.config.settings import Settings
from app.core.exceptions import ProviderConfigurationError


def _extract_message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
        return "".join(parts)
    return ""


class MistralAIProvider(BaseLLMProvider):
    name = "mistral"

    def __init__(self, settings: Settings, api_key: str | None = None) -> None:
        resolved_api_key = api_key or settings.mistral_api_key
        if not resolved_api_key:
            raise ProviderConfigurationError(self.name, "MISTRAL_API_KEY is missing")
        self._settings = settings
        self._client = Mistral(api_key=resolved_api_key)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or "mistral-small-latest"
        response = await asyncio.to_thread(
            self._client.chat.complete,
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        choices = getattr(response, "choices", [])
        text = ""
        if choices:
            message = getattr(choices[0], "message", None)
            if message is not None:
                text = _extract_message_text(getattr(message, "content", ""))
        usage_raw = getattr(response, "usage", None)
        usage = usage_raw.model_dump() if hasattr(usage_raw, "model_dump") else None
        return LLMResponse(text=text, model=model, usage=usage)

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        result = await self.generate(request)
        if result.text:
            yield result.text
