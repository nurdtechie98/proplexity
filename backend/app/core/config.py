"""
Configuration settings for the FastAPI application.
Loads environment variables and provides configuration settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # Base directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Database
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{BASE_DIR}/sql_app.db"

    # Scraping settings
    DEFAULT_MAX_URLS: int = 100
    DEFAULT_SCRAPE_INTERVAL_DAYS: int = 7

    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()


settings = Settings()
