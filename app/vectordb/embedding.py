from __future__ import annotations

import os
from typing import Any, Protocol

import httpx


class EmbeddingModel(Protocol):
    async def embed(self, text: str) -> list[float]: ...


class OpenAICompatibleEmbeddingModel:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        api_key_env: str | None,
        api_key_prefix: str,
        endpoint_path: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        normalized_base_url = base_url.strip()
        if not normalized_base_url.startswith(("http://", "https://")):
            normalized_base_url = f"http://{normalized_base_url}"

        self.base_url = normalized_base_url.rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(timeout_seconds)
        self.api_key_env = api_key_env
        self.api_key_prefix = api_key_prefix
        self.endpoint_path = endpoint_path
        self.extra_headers = extra_headers or {}

    async def embed(self, text: str) -> list[float]:
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key_env:
            api_key = os.getenv(self.api_key_env, "")
            if api_key:
                headers["Authorization"] = f"{self.api_key_prefix} {api_key}"

        url = f"{self.base_url}{self.endpoint_path}"
        body: dict[str, Any] = {"model": self.model, "input": text}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=body)

        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", [])
        if not data:
            return []

        embedding = data[0].get("embedding", [])
        return [float(value) for value in embedding]


class OllamaEmbeddingModel:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        endpoint_path: str,
    ) -> None:
        normalized_base_url = base_url.strip()
        if not normalized_base_url.startswith(("http://", "https://")):
            normalized_base_url = f"http://{normalized_base_url}"

        self.base_url = normalized_base_url.rstrip("/")
        self.model = model
        self.timeout = httpx.Timeout(timeout_seconds)
        self.endpoint_path = endpoint_path

    async def embed(self, text: str) -> list[float]:
        url = f"{self.base_url}{self.endpoint_path}"
        body = {"model": self.model, "prompt": text}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=body)

        response.raise_for_status()
        payload = response.json()
        embedding = payload.get("embedding", [])
        return [float(value) for value in embedding]
