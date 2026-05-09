from __future__ import annotations

from typing import Any

import httpx

from app.core.exceptions import ProviderRequestError
from app.domain.ports import ProviderOutput
from app.providers.base import BaseProvider


def _extract_ollama_text(payload: dict[str, Any]) -> str:
    message = payload.get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    return str(content)


class OllamaProvider(BaseProvider):
    async def generate(
        self,
        *,
        user_input: str,
        system_prompt: str | None,
        model: str | None,
        temperature: float,
        max_tokens: int | None,
        metadata: dict[str, object],
    ) -> ProviderOutput:
        base_url = (self.config.base_url or "http://localhost:11434").rstrip("/")
        endpoint_path = self.config.endpoint_path or "/api/chat"
        url = f"{base_url}{endpoint_path}"

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

        options: dict[str, object] = {"temperature": temperature}
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        body: dict[str, object] = {
            "model": model or self.config.default_model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        if metadata:
            body["metadata"] = metadata

        timeout = httpx.Timeout(self.config.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=body, headers=self.config.extra_headers)

        if response.status_code >= 400:
            raise ProviderRequestError(self.name, response.text)

        payload = response.json()
        text = _extract_ollama_text(payload)
        payload_model = payload.get("model")
        model_name = payload_model if isinstance(payload_model, str) else None
        return ProviderOutput(text=text, model=model_name or model or self.config.default_model, raw=payload)
