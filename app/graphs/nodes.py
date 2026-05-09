from __future__ import annotations

from app.domain.models import AIInvokeResponse
from app.graphs.state import AIState
from app.providers.factory import ProviderFactory


class AINodes:
    def __init__(self, provider_factory: ProviderFactory) -> None:
        self.provider_factory = provider_factory

    async def prepare(self, state: AIState) -> AIState:
        request = state["request"]
        selected_provider = request.provider or self.provider_factory.default_provider
        return {"provider_name": selected_provider}

    async def call_model(self, state: AIState) -> AIState:
        request = state["request"]
        provider = self.provider_factory.get(state["provider_name"])
        output = await provider.generate(
            user_input=request.input,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )
        return {"provider_output": output}

    async def finalize(self, state: AIState) -> AIState:
        output = state["provider_output"]
        response = AIInvokeResponse(
            output=output.text,
            provider=state["provider_name"],
            model=output.model,
            trace_id=state["trace_id"],
            raw=output.raw,
        )
        return {"response": response}
