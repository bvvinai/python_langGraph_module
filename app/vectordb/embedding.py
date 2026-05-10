from __future__ import annotations

import hashlib
import math
import os
from typing import Any, Protocol

import httpx


class EmbeddingModel(Protocol):
    async def embed(self, text: str) -> list[float]: ...


class HashEmbeddingModel:
    """Deterministic local embedding for development and tests."""

    def __init__(self, *, size: int) -> None:
        if size <= 0:
            raise ValueError("Embedding size must be greater than zero.")
        self.size = size

    async def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [0.0 for _ in range(self.size)]

        for idx, byte in enumerate(digest):
            slot = idx % self.size
            centered = (byte - 127.5) / 127.5
            vector[slot] += centered

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]


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
        self.base_url = base_url.rstrip("/")
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
        self.base_url = base_url.rstrip("/")
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
