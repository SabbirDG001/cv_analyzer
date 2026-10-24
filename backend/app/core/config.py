from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/skillbridge"
    frontend_origin: str = "http://localhost:3000"
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""
    gemini_api_key: str = ""
    llm_model: str = ""
    youtube_api_key: str = ""
    max_analyses_per_day: int = 10
    max_llm_calls_per_day: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
