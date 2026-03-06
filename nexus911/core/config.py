"""Global configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    FIRESTORE_DATABASE: str = "(default)"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = True
    APP_NAME: str = "Nexus911"
    MAX_CONCURRENT_CALLERS: int = 10
    DEDUP_SIMILARITY_THRESHOLD: float = 0.75
    INCIDENT_RADIUS_METERS: float = 500.0

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
