"""Application configuration module using Pydantic Settings.

Manages environment variables, secrets, database credentials, and runtime parameters.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings and environment variable definitions."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API Key")

    # Database Configuration
    POSTGRES_USER: str = Field(default="pipeline_user", description="PostgreSQL Username")
    POSTGRES_PASSWORD: str = Field(default="pipeline_password_secure_mock", description="PostgreSQL Password")
    POSTGRES_DB: str = Field(default="pipeline_db", description="PostgreSQL Database Name")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL Host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL Port")

    # Logging and Runtime Parameters
    LOG_LEVEL: str = Field(default="INFO", description="Loguru logging level (DEBUG, INFO, WARNING, ERROR)")
    HEADLESS_BROWSER: bool = Field(default=True, description="Whether Playwright runs in headless mode")

    @property
    def database_url(self) -> str:
        """Constructs synchronous PostgreSQL connection URI."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        """Constructs asynchronous PostgreSQL connection URI."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton instance of application settings."""
    return Settings()


settings = get_settings()
