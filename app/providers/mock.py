from __future__ import annotations

from app.domain.ports import ProviderOutput
from app.providers.base import BaseProvider


class MockProvider(BaseProvider):
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
        prompt_prefix = f"[{system_prompt}] " if system_prompt else ""
        text = (
            f"Mock response from {self.name}. "
            f"temperature={temperature}, max_tokens={max_tokens}. "
            f"{prompt_prefix}{user_input}"
        )
        return ProviderOutput(text=text, model=model or self.config.default_model, raw={"metadata": metadata})
