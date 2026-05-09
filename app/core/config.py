from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="LangGraph FastAPI Starter", alias="APP_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    default_provider: str = Field(default="mock", alias="DEFAULT_PROVIDER")
    providers_config_path: str = Field(default="config/providers.json", alias="PROVIDERS_CONFIG_PATH")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
