"""Typed application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "dev", "staging", "prod"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_DEFAULT_JWT_SECRET = "local-only-change-me-please-32-chars"
_INSECURE_JWT_SECRETS = {
    _DEFAULT_JWT_SECRET,
    "replace-with-at-least-32-random-characters",
}


class Settings(BaseSettings):
    """Application configuration resolved from ``.env`` and the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
        frozen=True,
    )

    app_name: str = "Code Battle"
    app_env: Environment = "local"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = False
    log_level: LogLevel = "INFO"
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://code_battle:code_battle@localhost:5432/code_battle"
    sql_echo: bool = False
    postgres_pool_size: int = Field(default=5, ge=1)
    postgres_max_overflow: int = Field(default=10, ge=0)
    postgres_pool_timeout_seconds: float = Field(default=30.0, gt=0)

    mongodb_url: str = (
        "mongodb://code_battle:code_battle@localhost:27017/?authSource=admin"
    )
    mongodb_database: str = "code_battle_tests"
    mongodb_server_selection_timeout_ms: int = Field(default=5_000, gt=0)

    redis_url: str = "redis://localhost:6380/0"
    celery_broker_url: str = "redis://localhost:6380/0"
    celery_result_backend: str = "redis://localhost:6380/1"

    jwt_secret_key: SecretStr = SecretStr(_DEFAULT_JWT_SECRET)
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, gt=0)
    jwt_refresh_token_expire_days: int = Field(default=30, gt=0)

    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    cors_allow_credentials: bool = True

    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        """Keep API prefixes consistent for router registration."""
        normalized = f"/{value.strip('/')}"
        if normalized == "/":
            raise ValueError(
                "API_PREFIX must contain at least one path segment"
            )
        return normalized

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        """Allow conventional lowercase log levels in environment files."""
        return value.upper() if isinstance(value, str) else value

    @field_validator("cors_allow_origins")
    @classmethod
    def normalize_cors_origins(cls, origins: list[str]) -> list[str]:
        """Strip trailing slashes, empty values, and duplicates."""
        normalized = [
            origin.strip().rstrip("/") for origin in origins if origin.strip()
        ]
        if not normalized:
            raise ValueError(
                "CORS_ALLOW_ORIGINS must contain at least one origin"
            )
        return list(dict.fromkeys(normalized))

    @model_validator(mode="after")
    def validate_deployment_secret(self) -> Self:
        """Prevent deployed environments from using an example JWT secret."""
        secret = self.jwt_secret_key.get_secret_value()
        if self.app_env in {"staging", "prod"} and (
            secret in _INSECURE_JWT_SECRETS or len(secret) < 32
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be a unique secret of at least "
                "32 characters in staging and production"
            )
        return self

    @property
    def is_production(self) -> bool:
        """Return whether production-specific behavior should be enabled."""
        return self.app_env == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one immutable settings instance per process."""
    return Settings()
