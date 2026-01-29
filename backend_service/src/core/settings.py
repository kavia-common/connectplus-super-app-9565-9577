from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables required (to be provided via .env by orchestrator):
    - MONGODB_URI
    - MONGODB_DB
    - AI_ENGINE_BASE_URL
    - JWT_SECRET (for minimal JWT verification)
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_uri: str = Field(..., alias="MONGODB_URI", description="MongoDB connection URI.")
    mongodb_db: str = Field(..., alias="MONGODB_DB", description="MongoDB database name.")
    ai_engine_base_url: str = Field(
        ...,
        alias="AI_ENGINE_BASE_URL",
        description="Base URL of the ai_nlp_engine service (e.g., http://ai_nlp_engine:8000).",
    )

    jwt_secret: str = Field(
        "dev-only-change-me",
        alias="JWT_SECRET",
        description="JWT secret for token verification (placeholder for template).",
    )
    jwt_algorithm: str = Field(
        "HS256",
        alias="JWT_ALGORITHM",
        description="JWT algorithm for token verification.",
    )

    chat_rate_limit_per_minute: int = Field(
        20,
        alias="CHAT_RATE_LIMIT_PER_MINUTE",
        description="Max /chat/send calls per user per rolling minute (in-memory limiter).",
    )


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings: Parsed settings from environment variables.
    """
    return Settings()
