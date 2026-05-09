from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.ports import ProviderOutput
from app.providers.registry import ProviderConfig


class BaseProvider(ABC):
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.name = config.name

    @abstractmethod
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
        raise NotImplementedError
