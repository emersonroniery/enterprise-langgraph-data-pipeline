"""Application configuration module using Pydantic Settings.

Loads environment variables, secrets, database credentials, and execution parameters.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for the market intelligence pipeline."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys & Secrets
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API Key for LLM-based competitive intelligence analysis",
    )
    ANTHROPIC_API_KEY: str | None = Field(
        default=None,
        description="Anthropic API Key as alternative LLM provider",
    )

    # Database Configuration
    POSTGRES_URL: str = Field(
        default="postgresql://pipeline_user:pipeline_password_secure_mock@localhost:5432/pipeline_db",
        description="PostgreSQL connection URI for relational data persistence",
    )

    # Pipeline Execution Settings
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    REQUEST_TIMEOUT: float = Field(
        default=15.0,
        description="HTTP request timeout in seconds for web extractions",
    )
    MAX_RETRIES: int = Field(
        default=2,
        description="Maximum retry threshold when confidence score is sub-optimal",
    )
    MIN_CONFIDENCE_THRESHOLD: float = Field(
        default=0.7,
        description="Minimum confidence score required to finalize pipeline execution",
    )
    DEFAULT_USER_AGENT: str = Field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        description="Default HTTP User-Agent header for web scrapers",
    )


@lru_cache
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()


settings = get_settings()
