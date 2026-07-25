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

    # WS02 Market Data Platform providers (engines never call these directly)
    indian_api_key: str = ""
    indian_api_base_url: str = "https://stock.indianapi.in"
    finnhub_api_key: str = ""
    finnhub_base_url: str = "https://finnhub.io/api/v1"
    fmp_api_key: str = ""
    fmp_base_url: str = "https://financialmodelingprep.com/api/v3"

    # E01 Macro & Regime Engine feature flags (P0 defaults)
    e01_p0: bool = True
    e01_hmm: bool = False
    e01_ml: bool = False

    # E14 Risk & Crowding Overlay feature flags (P0 defaults)
    e14_p0: bool = True
    e14_ml: bool = False
    e14_bayes: bool = False

    # E02 Factor & Style Engine feature flags (P0 defaults)
    e02_p0: bool = True
    e02_timing: bool = False
    e02_rotation: bool = False
    e02_smart_beta: bool = False
    e02_ml: bool = False

    # E03 Cross-Sectional Quant Engine feature flags (P0/M0 defaults)
    e03_p0: bool = True
    e03_parity: bool = True
    e03_composite: bool = False
    e03_xs_mode: bool = False
    e03_ml: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
