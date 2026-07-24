from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8100

    # Shared service auth between Node gateway and this engine
    intelligence_engine_token: str = "dev-intelligence-token"

    # AGIB Node cached APIs (agents must not call third-party APIs directly)
    agib_api_base_url: str = "http://127.0.0.1:3001"
    agib_service_token: str = ""

    # Optional OpenAI for Phase 2 CIO synthesis (stub works without it)
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    # Supabase / Postgres (optional — falls back to in-memory store)
    database_url: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Embedding dimension for pgvector (text-embedding-3-small)
    embedding_dimensions: int = 1536


@lru_cache
def get_settings() -> Settings:
    return Settings()
