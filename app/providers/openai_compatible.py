from __future__ import annotations

import os
from typing import Any

import httpx

from app.core.exceptions import ProviderAuthError, ProviderRequestError
from app.domain.ports import ProviderOutput
from app.providers.base import BaseProvider


def _extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")))
        return "\n".join(part for part in text_parts if part)

    return str(content)


class OpenAICompatibleProvider(BaseProvider):
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

        base_url = (self.config.base_url or "https://api.openai.com").rstrip("/")
        url = f"{base_url}/v1/chat/completions"

        headers = {"Content-Type": "application/json", **self.config.extra_headers}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

        body: dict[str, object] = {
            "model": model or self.config.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        if metadata:
            body["metadata"] = metadata
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        timeout = httpx.Timeout(self.config.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=body, headers=headers)

        if response.status_code >= 400:
            raise ProviderRequestError(self.name, response.text)

        payload = response.json()
        text = _extract_text(payload)
        return ProviderOutput(text=text, model=payload.get("model"), raw=payload)
