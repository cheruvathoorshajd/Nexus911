"""Global configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    GOOGLE_GENAI_USE_VERTEXAI: bool = False
    FIRESTORE_DATABASE: str = "(default)"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = True
    APP_NAME: str = "Nexus911"
    MAX_CONCURRENT_CALLERS: int = 10
    DEDUP_SIMILARITY_THRESHOLD: float = 0.55
    INCIDENT_RADIUS_METERS: float = 200.0
    VERIFYLAYER_ENABLED: bool = True
    VERIFYLAYER_LATENCY_BUDGET_MS: int = 200
    VERIFYLAYER_CACHE_SIZE: int = 1024
    VERIFYLAYER_CACHE_TTL: float = 300.0
    VERIFICATION_MODEL: str = "gemini-2.5-flash"

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def create_genai_client():
    """Create a google-genai client using either Vertex AI or API key."""
    from google import genai
    if settings.GOOGLE_GENAI_USE_VERTEXAI:
        return genai.Client(
            vertexai=True,
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
        )
    return genai.Client(api_key=settings.GOOGLE_API_KEY)
