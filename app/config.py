from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Pydantic will automatically read from .env file and
    validate that required variables are present.
    """

    app_name: str = "AI Sales Outreach API"
    app_env: str = "development"
    debug: bool = True

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # LLM APIs (optional for now, we'll add later)
    gemini_api_key: str = ""

    # External Services (optional for now)
    serper_api_key: str = ""
    rapidapi_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Using lru_cache to ensure settings are only loaded once.
    """
    return Settings()
