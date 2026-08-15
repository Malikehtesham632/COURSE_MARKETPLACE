"""
Application settings, loaded from environment variables / the .env file.

Uses pydantic-settings so every value is type-checked at startup instead
of silently being read as a plain string that could be wrong.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Sensible local defaults, overridden by whatever is in .env.
    database_url: str = "sqlite:///./course_marketplace.db"
    secret_key: str = "dev_secret_key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
