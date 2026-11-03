from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mistral_api_key: str
    mistral_model: str = "mistral-large-4"
    mistral_url: str = "https://api.mistral.ai/v1/chat/completions"
    request_timeout: float = 60.0
    max_retries: int = 2
    max_input_chars: int = 50_000


@lru_cache
def get_settings() -> Settings:
    return Settings()