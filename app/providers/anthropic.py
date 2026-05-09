from __future__ import annotations

import os
from typing import Any

import httpx

from app.core.exceptions import ProviderAuthError, ProviderRequestError
from app.domain.ports import ProviderOutput
from app.providers.base import BaseProvider


def _extract_anthropic_text(payload: dict[str, Any]) -> str:
    content = payload.get("content", [])
    if not isinstance(content, list):
        return ""

    text_parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            text_value = item.get("text", "")
            if isinstance(text_value, str) and text_value:
                text_parts.append(text_value)

    return "\n".join(text_parts)


class AnthropicProvider(BaseProvider):
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
        api_key_env = self.config.api_key_env
        api_key = os.getenv(api_key_env, "") if api_key_env else ""
        if api_key_env and not api_key:
            raise ProviderAuthError(self.name)

        base_url = (self.config.base_url or "https://api.anthropic.com").rstrip("/")
        endpoint_path = self.config.endpoint_path or "/v1/messages"
        url = f"{base_url}{endpoint_path}"

        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            **self.config.extra_headers,
        }

        body: dict[str, object] = {
            "model": model or self.config.default_model,
            "messages": [{"role": "user", "content": user_input}],
            "temperature": temperature,
            "max_tokens": max_tokens if max_tokens is not None else 1024,
        }
        if system_prompt:
            body["system"] = system_prompt
        if metadata:
            body["metadata"] = metadata

        timeout = httpx.Timeout(self.config.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=body, headers=headers)

        if response.status_code >= 400:
            raise ProviderRequestError(self.name, response.text)

        payload = response.json()
        text = _extract_anthropic_text(payload)
        payload_model = payload.get("model")
        model_name = payload_model if isinstance(payload_model, str) else None
        return ProviderOutput(text=text, model=model_name or model or self.config.default_model, raw=payload)
