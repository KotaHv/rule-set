"""
Configuration settings for the rule-set project.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment configuration
    environment: Literal["development", "production"] = Field(
        default="production", description="Application environment"
    )

    # Output directory configuration
    build_dir: Path = Field(
        default=ROOT_DIR / "rule-set",
        description="Output directory for rule sets",
    )

    # Cache configuration
    cache_dir: Path = Field(default=ROOT_DIR / ".cache", description="Cache directory")

    cache_ttl_hours: int = Field(default=1, ge=0, description="Cache TTL in hours")

    # HTTP configuration
    http_timeout: int = Field(
        default=10, gt=0, description="HTTP request timeout in seconds"
    )

    http_max_retries: int = Field(
        default=5, ge=0, description="Maximum HTTP retry attempts"
    )

    http_verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    @field_validator("http_verify_ssl", mode="after")
    def set_http_verify_ssl(cls, _: bool, info: ValidationInfo) -> bool:
        print(info)
        if info.data["environment"] == "development":
            return False
        return True


# Global settings instance
settings = Settings()
settings.build_dir.mkdir(exist_ok=True)
settings.cache_dir.mkdir(exist_ok=True)
