"""
Configuration settings for the rule-set project.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Environment configuration
    environment: Literal["development", "production"] = Field(
        default="production", description="Application environment"
    )

    # Output directory configuration
    dir_path: Path = Field(
        default=Path("rule-set"), description="Output directory for rule sets"
    )

    # Cache configuration
    cache_dir: Path = Field(default=Path(".cache"), description="Cache directory")

    cache_ttl_hours: int = Field(default=1, ge=0, description="Cache TTL in hours")

    # HTTP configuration
    http_timeout: int = Field(
        default=10, gt=0, description="HTTP request timeout in seconds"
    )

    http_max_retries: int = Field(
        default=5, ge=0, description="Maximum HTTP retry attempts"
    )

    http_verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.dir_path.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        # Set SSL verification based on environment
        if self.environment == "development":
            self.http_verify_ssl = False
        else:
            self.http_verify_ssl = True


# Global settings instance
settings = Settings()
