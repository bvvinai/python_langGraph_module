from __future__ import annotations

from collections.abc import AsyncGenerator

from anthropic import AsyncAnthropic

from app.contracts.providers import BaseLLMProvider, LLMRequest, LLMResponse
from app.config.settings import Settings
from app.core.exceptions import ProviderConfigurationError


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(
        self,
        settings: Settings,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        resolved_api_key = api_key or settings.anthropic_api_key
        if not resolved_api_key:
            raise ProviderConfigurationError(self.name, "ANTHROPIC_API_KEY is missing")
        self._settings = settings
        if not base_url:
            self._client = AsyncAnthropic(api_key=resolved_api_key)
            return

        try:
            self._client = AsyncAnthropic(api_key=resolved_api_key, base_url=base_url)
        except TypeError as exc:
            raise ProviderConfigurationError(
                self.name,
                "base_url override is not supported by the installed anthropic SDK version",
            ) from exc

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or "claude-3-5-haiku-latest"
        response = await self._client.messages.create(
            model=model,
            max_tokens=request.max_tokens or 1024,
            temperature=request.temperature,
            messages=[
                {
                    "role": m.role if m.role in {"user", "assistant"} else "user",
                    "content": m.content,
                }
                for m in request.messages
            ],
        )

        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        usage_raw = getattr(response, "usage", None)
        usage = usage_raw.model_dump() if hasattr(usage_raw, "model_dump") else None
        return LLMResponse(text=text, model=getattr(response, "model", model), usage=usage)

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        result = await self.generate(request)
        if result.text:
            yield result.text
