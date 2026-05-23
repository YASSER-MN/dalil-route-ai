from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openrouter_api_key: str = ""  # primary LLM — DeepSeek V3 via openrouter.ai (free)
    groq_api_key: str = ""        # kept for fallback
    admin_key: str = "changeme"
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
