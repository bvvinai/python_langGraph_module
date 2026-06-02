from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx

from app.contracts.providers import BaseLLMProvider, LLMRequest, LLMResponse
from app.config.settings import Settings


class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(self, settings: Settings, base_url: str | None = None) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=base_url or settings.ollama_base_url,
            timeout=120.0,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or "llama3.1:8b"
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
            },
        }
        response = await self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        text = data.get("message", {}).get("content", "")
        return LLMResponse(text=text, model=model, usage=None)

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        model = request.model or "llama3.1:8b"
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": True,
            "options": {
                "temperature": request.temperature,
            },
        }
        async with self._client.stream("POST", "/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                row = json.loads(line)
                if "message" in row and "content" in row["message"]:
                    chunk = row["message"]["content"]
                    if chunk:
                        yield chunk
