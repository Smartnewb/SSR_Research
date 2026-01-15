"""Application configuration."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SSR Market Research API"
    debug: bool = False
    version: str = "1.0.0"

    openai_api_key: Optional[str] = None

    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    max_sample_size: int = 200
    min_sample_size: int = 5

    reasoning_effort: Optional[str] = None
    verbosity: Optional[str] = None
    max_output_tokens: Optional[int] = None
    enable_caching: Optional[bool] = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
