from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration, populated from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_api_key: str | None = None
    elasticsearch_index: str = "documents"

    # LLM - any OpenAI-compatible endpoint (Anthropic-through-a-gateway, an
    # internal company hub, Azure OpenAI, vLLM, etc.). base_url=None uses
    # OpenAI's own default endpoint.
    llm_api_key: str
    llm_base_url: str | None = None
    llm_model: str = "claude-sonnet-4-6"

    # App
    app_env: str = "development"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
