"""
config.py - Loads settings (database passwords, ports, etc.) from the .env file.

Why: secrets like passwords must NEVER be written directly in code,
because code goes to GitHub. The .env file stays on your Mac only.
"""

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

# Find the project root, where the .env file lives.
# This file is at: seat-booking-system/backend/app/config.py
#   parents[0] = app, parents[1] = backend, parents[2] = seat-booking-system
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """All settings our app needs. Values are read from .env automatically."""

    # ---- PostgreSQL ----
    # No default values for these: if .env is missing them, the app
    # fails immediately with a clear error instead of failing later.
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # ---- Redis ----
    redis_host: str = "localhost"
    redis_port: int = 6379

    # ---- Business rules ----
    seat_hold_seconds: int = 300  # 5-minute seat hold

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unrelated lines in .env
    )

    @property
    def database_url(self) -> str:
        """Full address SQLAlchemy uses to connect to PostgreSQL."""
        # quote_plus makes special characters in passwords (like @ or /) safe.
        return (
            f"postgresql+psycopg://{quote_plus(self.postgres_user)}:"
            f"{quote_plus(self.postgres_password)}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Full address the Redis client uses to connect."""
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    """Create the settings once and reuse the same copy everywhere."""
    return Settings()
