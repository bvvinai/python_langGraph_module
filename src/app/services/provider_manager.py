from __future__ import annotations

import os
from collections.abc import Callable
from typing import TypeVar

from app.contracts.providers import (
    BaseEmbeddingProvider,
    BaseGraphStore,
    BaseLLMProvider,
    EmbeddingRequest,
    EmbeddingResponse,
    LLMRequest,
    LLMResponse,
    BaseVectorStore,
)
from app.config.settings import Settings
from app.core.embedding_provider_config import (
    EmbeddingProvidersConfig,
    load_embedding_providers_config,
)
from app.core.exceptions import (
    ProviderConfigurationError,
    ProviderDisabledError,
    ProviderNotFoundError,
)
from app.core.llm_provider_config import LLMProvidersConfig, load_llm_providers_config
from app.providers.embeddings.ollama_embeddings import OllamaEmbeddingProvider
from app.providers.embeddings.openai_embeddings import OpenAIEmbeddingProvider
from app.providers.graphdb.neo4j_store import Neo4jGraphStore
from app.providers.llm.anthropic_provider import AnthropicProvider
from app.providers.llm.google_genai_provider import GoogleGenAIProvider
from app.providers.llm.groq_provider import GroqProvider
from app.providers.llm.ollama_provider import OllamaProvider
from app.providers.llm.openai_provider import OpenAIProvider
from app.providers.vectordb.qdrant_store import QdrantVectorStore

TProvider = TypeVar("TProvider")


class ConfiguredLLMModel(BaseLLMProvider):
    def __init__(
        self,
        model_key: str,
        backend: BaseLLMProvider,
        default_model_name: str | None,
    ) -> None:
        self.name = model_key
        self._backend = backend
        self._default_model_name = default_model_name

    def _with_default_model(self, request: LLMRequest) -> LLMRequest:
        if request.model or not self._default_model_name:
            return request

        return LLMRequest(
            messages=request.messages,
            model=self._default_model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        return await self._backend.generate(self._with_default_model(request))

    async def stream_generate(self, request: LLMRequest):
        async for token in self._backend.stream_generate(self._with_default_model(request)):
            yield token


class ConfiguredEmbeddingModel(BaseEmbeddingProvider):
    def __init__(
        self,
        model_key: str,
        backend: BaseEmbeddingProvider,
        default_model_name: str | None,
    ) -> None:
        self.name = model_key
        self._backend = backend
        self._default_model_name = default_model_name

    def _with_default_model(self, request: EmbeddingRequest) -> EmbeddingRequest:
        if request.model or not self._default_model_name:
            return request

        return EmbeddingRequest(
            texts=request.texts,
            model=self._default_model_name,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        return await self._backend.embed(self._with_default_model(request))


class ProviderManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._instances: dict[str, object] = {}
        self._llm_config: LLMProvidersConfig = load_llm_providers_config(
            config_path=settings.llm_provider_config_path,
            fallback_default_provider="openai_default",
        )
        self._embedding_config: EmbeddingProvidersConfig = load_embedding_providers_config(
            config_path=settings.embedding_provider_config_path,
            fallback_default_provider=settings.default_embedding_provider,
        )

        self._llm_builders: dict[str, Callable[[], BaseLLMProvider]] = {}
        self._llm_enabled: dict[str, bool] = {}
        self._embedding_builders: dict[str, Callable[[], BaseEmbeddingProvider]] = {}
        self._embedding_enabled: dict[str, bool] = {}
        self._vector_builders: dict[str, Callable[[], BaseVectorStore]] = {}
        self._vector_enabled: dict[str, bool] = {}
        self._graph_builders: dict[str, Callable[[], BaseGraphStore]] = {}
        self._graph_enabled: dict[str, bool] = {}

        self._register_all()

    @staticmethod
    def _register_provider(
        builders: dict[str, Callable[[], TProvider]],
        enabled_map: dict[str, bool],
        name: str,
        builder: Callable[[], TProvider],
        enabled: bool,
    ) -> None:
        builders[name] = builder
        enabled_map[name] = enabled

    @staticmethod
    def _resolve_provider(
        builders: dict[str, Callable[[], TProvider]],
        enabled_map: dict[str, bool],
        name: str,
    ) -> TProvider:
        if name not in builders:
            raise ProviderNotFoundError(name)
        if not enabled_map.get(name, False):
            raise ProviderDisabledError(name)
        return builders[name]()

    def _cached(self, key: str, builder):
        if key not in self._instances:
            self._instances[key] = builder()
        return self._instances[key]

    def _llm_builder(self, backend_name: str, base_url: str | None, api_key: str | None):
        builders = {
            "openai": lambda: self._cached(
                f"llm_openai::{base_url or 'default'}::{api_key or 'none'}",
                lambda: OpenAIProvider(self._settings, base_url=base_url, api_key=api_key),
            ),
            "anthropic": lambda: self._cached(
                f"llm_anthropic::{base_url or 'default'}::{api_key or 'none'}",
                lambda: AnthropicProvider(self._settings, base_url=base_url, api_key=api_key),
            ),
            "google_genai": lambda: self._cached(
                f"llm_google_genai::{api_key or 'none'}",
                lambda: GoogleGenAIProvider(self._settings, api_key=api_key),
            ),
            "mistral": lambda: self._cached(
                f"llm_mistral::{api_key or 'none'}",
                lambda: self._build_mistral_provider(api_key=api_key),
            ),
            "groq": lambda: self._cached(
                f"llm_groq::{api_key or 'none'}",
                lambda: GroqProvider(self._settings, api_key=api_key),
            ),
            "ollama": lambda: self._cached(
                f"llm_ollama::{base_url or 'default'}",
                lambda: OllamaProvider(self._settings, base_url=base_url),
            ),
        }
        return builders.get(backend_name)

    def _build_mistral_provider(self, api_key: str | None) -> BaseLLMProvider:
        try:
            from app.providers.llm.mistral_provider import MistralAIProvider
        except ImportError as exc:
            raise ProviderConfigurationError(
                "mistral",
                (
                    "Mistral SDK import failed. Install a compatible 'mistralai' package "
                    "or disable mistral models in llm_providers.json"
                ),
            ) from exc

        return MistralAIProvider(self._settings, api_key=api_key)

    def _embedding_builder(self, backend_name: str, base_url: str | None, api_key: str | None):
        builders = {
            "openai": lambda: self._cached(
                f"emb_openai::{base_url or 'default'}::{api_key or 'none'}",
                lambda: OpenAIEmbeddingProvider(
                    self._settings,
                    base_url=base_url,
                    api_key=api_key,
                ),
            ),
            "ollama": lambda: self._cached(
                f"emb_ollama::{base_url or 'default'}",
                lambda: OllamaEmbeddingProvider(self._settings, base_url=base_url),
            ),
        }
        return builders.get(backend_name)

    @staticmethod
    def _default_api_key_env(backend_name: str) -> str | None:
        return {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google_genai": "GOOGLE_GENAI_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "groq": "GROQ_API_KEY",
        }.get(backend_name)

    def _resolve_api_key(self, backend_name: str, configured_env_var: str | None) -> str | None:
        env_var_name = configured_env_var or self._default_api_key_env(backend_name)
        if not env_var_name:
            return None

        value = os.getenv(env_var_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    @staticmethod
    def _default_embedding_api_key_env(backend_name: str) -> str | None:
        return {
            "openai": "OPENAI_API_KEY",
        }.get(backend_name)

    def _resolve_embedding_api_key(self, backend_name: str, configured_env_var: str | None) -> str | None:
        env_var_name = configured_env_var or self._default_embedding_api_key_env(backend_name)
        if not env_var_name:
            return None

        value = os.getenv(env_var_name)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _build_configured_llm_model(
        self,
        model_key: str,
        backend_name: str,
        model_name: str | None,
        base_url: str | None,
        api_key_env: str | None,
    ) -> BaseLLMProvider:
        if base_url and backend_name not in {"openai", "anthropic", "ollama"}:
            raise ProviderConfigurationError(
                model_key,
                (
                    f"base_url is configured for backend '{backend_name}', "
                    "but this backend does not currently support base_url override"
                ),
            )

        resolved_api_key = self._resolve_api_key(backend_name, configured_env_var=api_key_env)
        required_api_env = api_key_env or self._default_api_key_env(backend_name)
        if required_api_env and not resolved_api_key:
            raise ProviderConfigurationError(
                model_key,
                f"Missing API key. Set the '{required_api_env}' environment variable",
            )

        builder = self._llm_builder(
            backend_name,
            base_url=base_url,
            api_key=resolved_api_key,
        )
        if builder is None:
            raise ProviderConfigurationError(
                model_key,
                f"Unknown LLM backend '{backend_name}' in LLM provider config",
            )

        backend = builder()
        return ConfiguredLLMModel(
            model_key=model_key,
            backend=backend,
            default_model_name=model_name,
        )

    def _build_configured_embedding_model(
        self,
        model_key: str,
        backend_name: str,
        model_name: str | None,
        base_url: str | None,
        api_key_env: str | None,
    ) -> BaseEmbeddingProvider:
        if base_url and backend_name not in {"openai", "ollama"}:
            raise ProviderConfigurationError(
                model_key,
                (
                    f"base_url is configured for backend '{backend_name}', "
                    "but this backend does not currently support base_url override"
                ),
            )

        resolved_api_key = self._resolve_embedding_api_key(
            backend_name,
            configured_env_var=api_key_env,
        )
        required_api_env = api_key_env or self._default_embedding_api_key_env(backend_name)
        if required_api_env and not resolved_api_key:
            raise ProviderConfigurationError(
                model_key,
                f"Missing API key. Set the '{required_api_env}' environment variable",
            )

        builder = self._embedding_builder(
            backend_name,
            base_url=base_url,
            api_key=resolved_api_key,
        )
        if builder is None:
            raise ProviderConfigurationError(
                model_key,
                f"Unknown embedding backend '{backend_name}' in embeddings config",
            )

        backend = builder()
        return ConfiguredEmbeddingModel(
            model_key=model_key,
            backend=backend,
            default_model_name=model_name,
        )

    def _register_llm_providers(self) -> None:
        for model_key, model_entry in self._llm_config.providers.items():
            enabled = model_entry.enabled
            self._register_provider(
                self._llm_builders,
                self._llm_enabled,
                model_key,
                lambda model_key=model_key, model_entry=model_entry: self._cached(
                    f"llm_model_{model_key}",
                    lambda: self._build_configured_llm_model(
                        model_key=model_key,
                        backend_name=model_entry.backend,
                        model_name=model_entry.model,
                        base_url=model_entry.base_url,
                        api_key_env=model_entry.api_key_env,
                    ),
                ),
                enabled=enabled,
            )

    def _embedding_backend_enabled(self, backend_name: str) -> bool:
        return {
            "openai": self._settings.enable_embedding_openai,
            "ollama": self._settings.enable_embedding_ollama,
        }.get(backend_name, True)

    def _register_embedding_providers(self) -> None:
        for model_key, model_entry in self._embedding_config.providers.items():
            enabled = model_entry.enabled and self._embedding_backend_enabled(model_entry.backend)
            self._register_provider(
                self._embedding_builders,
                self._embedding_enabled,
                model_key,
                lambda model_key=model_key, model_entry=model_entry: self._cached(
                    f"embedding_model_{model_key}",
                    lambda: self._build_configured_embedding_model(
                        model_key=model_key,
                        backend_name=model_entry.backend,
                        model_name=model_entry.model,
                        base_url=model_entry.base_url,
                        api_key_env=model_entry.api_key_env,
                    ),
                ),
                enabled=enabled,
            )

    def _register_all(self) -> None:
        self._register_llm_providers()
        self._register_embedding_providers()

        self._register_provider(
            self._vector_builders,
            self._vector_enabled,
            "qdrant",
            lambda: self._cached("vector_qdrant", lambda: QdrantVectorStore(self._settings)),
            enabled=self._settings.enable_vector_qdrant and self._settings.enable_vectordb,
        )
        self._register_provider(
            self._vector_builders,
            self._vector_enabled,
            "chroma",
            lambda: self._cached("vector_chroma", self._build_chroma),
            enabled=self._settings.enable_vector_chroma and self._settings.enable_vectordb,
        )
        self._register_provider(
            self._graph_builders,
            self._graph_enabled,
            "neo4j",
            lambda: self._cached("graph_neo4j", lambda: Neo4jGraphStore(self._settings)),
            enabled=self._settings.enable_graph_neo4j and self._settings.enable_graphdb,
        )

    def _build_chroma(self) -> BaseVectorStore:
        from app.providers.vectordb.chroma_store import ChromaVectorStore

        return ChromaVectorStore(self._settings)

    def get_llm(self, provider: str | None) -> BaseLLMProvider:
        resolved_provider = self._llm_config.resolve_provider(provider)
        if resolved_provider is None:
            resolved_provider = self._llm_config.default_provider
        return self._resolve_provider(self._llm_builders, self._llm_enabled, resolved_provider)

    def get_embedding(self, provider: str | None) -> BaseEmbeddingProvider:
        if provider is None:
            resolved_provider = self._embedding_config.default_provider
        else:
            resolved_provider = self._embedding_config.resolve_provider(provider)
            if resolved_provider is None:
                resolved_provider = str(provider).strip().lower()
        return self._resolve_provider(self._embedding_builders, self._embedding_enabled, resolved_provider)

    def get_vector_store(self) -> BaseVectorStore:
        return self._resolve_provider(
            self._vector_builders,
            self._vector_enabled,
            self._settings.default_vector_store,
        )

    @property
    def default_vector_collection(self) -> str:
        return self._settings.default_vector_collection

    def get_graph_store(self, name: str = "neo4j") -> BaseGraphStore:
        return self._resolve_provider(self._graph_builders, self._graph_enabled, name)

    def available(self) -> dict[str, dict[str, bool]]:
        return {
            "llm": dict(self._llm_enabled),
            "embeddings": dict(self._embedding_enabled),
            "vectordb": dict(self._vector_enabled),
            "graphdb": dict(self._graph_enabled),
        }
