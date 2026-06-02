from __future__ import annotations

from app.config.settings import Settings
from app.core.embedding_provider_config import load_embedding_providers_config
from app.core.llm_provider_config import load_llm_providers_config


def build_capabilities(settings: Settings) -> dict[str, object]:
    llm_config = load_llm_providers_config(
        config_path=settings.llm_provider_config_path,
        fallback_default_provider="openai_default",
    )
    embedding_config = load_embedding_providers_config(
        config_path=settings.embedding_provider_config_path,
        fallback_default_provider=settings.default_embedding_provider,
    )

    llm_models: dict[str, dict[str, object]] = {}
    for model_key, model_entry in llm_config.providers.items():
        llm_models[model_key] = {
            "enabled": bool(model_entry.enabled),
            "backend": model_entry.backend,
            "model": model_entry.model,
            "base_url": model_entry.base_url,
            "api_key_env": model_entry.api_key_env,
            "aliases": list(model_entry.aliases),
        }

    embedding_models: dict[str, dict[str, object]] = {}
    backend_enabled_overrides = {
        "openai": settings.enable_embedding_openai,
        "ollama": settings.enable_embedding_ollama,
    }
    for model_key, model_entry in embedding_config.providers.items():
        backend_enabled = backend_enabled_overrides.get(model_entry.backend, True)
        embedding_models[model_key] = {
            "enabled": bool(model_entry.enabled and backend_enabled),
            "backend": model_entry.backend,
            "model": model_entry.model,
            "base_url": model_entry.base_url,
            "api_key_env": model_entry.api_key_env,
            "aliases": list(model_entry.aliases),
        }

    return {
        "service": settings.app_name,
        "environment": settings.app_env,
        "features": {
            "rest": settings.enable_rest,
            "websocket": settings.enable_websocket,
            "grpc": settings.enable_grpc,
            "ingestion": settings.enable_ingestion,
            "vectordb": settings.enable_vectordb,
            "graphdb": settings.enable_graphdb,
        },
        "providers": {
            "llm": {
                "models": llm_models,
                "default": llm_config.default_provider,
                "config_path": settings.llm_provider_config_path,
            },
            "embeddings": {
                "models": embedding_models,
                "openai": settings.enable_embedding_openai,
                "ollama": settings.enable_embedding_ollama,
                "default": embedding_config.default_provider,
                "config_path": settings.embedding_provider_config_path,
            },
            "vectordb": {
                "qdrant": settings.enable_vector_qdrant,
                "chroma": settings.enable_vector_chroma,
                "default": settings.default_vector_store,
            },
            "graphdb": {
                "neo4j": settings.enable_graph_neo4j,
            },
        },
    }
