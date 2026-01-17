"""Application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory (my-project/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env file into os.environ BEFORE pydantic_settings reads it
# This ensures os.getenv() calls in other modules (e.g., src/pipeline.py) work correctly
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SSR Market Research API"
    debug: bool = False
    version: str = "1.0.0"

    openai_api_key: Optional[str] = None

    llm_model: str = "gpt-5-nano"
    survey_model: str = "gpt-5-nano"
    survey_reasoning_effort: str = "none"
    analysis_model: str = "gpt-5.2"
    analysis_reasoning_effort: str = "high"
    analysis_verbosity: str = "medium"
    research_model: str = "gpt-5.2"
    research_reasoning_effort: str = "medium"
    product_model: str = "gpt-5-nano"
    embedding_model: str = "text-embedding-3-small"

    # Multi-Archetype Stratified Sampling Pipeline (v2.0)
    segmentation_model: str = "gpt-5.2"
    segmentation_reasoning_effort: str = "high"
    enrichment_model: str = "gpt-5-mini"
    enrichment_verbosity: str = "high"
    default_sample_size: int = 1000

    # QIE (Qualitative Insight Engine) v2.0 - Two-Tier Map-Reduce
    # Tier 1: Data structuring (gpt-5-mini) - fast, cost-effective
    qie_tier1_model: str = "gpt-5-mini"
    qie_tier1_reasoning_effort: str = "none"  # Speed optimization
    qie_tier1_verbosity: str = "low"  # JSON output stability
    qie_tier1_batch_size: int = 10  # Concurrent requests (rate limit aware)
    qie_tier1_max_retries: int = 3

    # Tier 2: Insight synthesis (gpt-5.2) - deep reasoning
    qie_tier2_model: str = "gpt-5.2"
    qie_tier2_reasoning_effort: str = "medium"  # Logical reasoning enabled
    qie_tier2_verbosity: str = "medium"  # Detailed report output
    qie_tier2_max_output_tokens: int = 4000

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    max_sample_size: int = 10000
    min_sample_size: int = 10

    reasoning_effort: Optional[str] = None
    verbosity: Optional[str] = None
    max_output_tokens: Optional[int] = None
    enable_caching: Optional[bool] = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
