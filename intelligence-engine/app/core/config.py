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

    # L4 Composite Intelligence feature flags (P0 Shadow defaults)
    l4_shadow: bool = True
    l4_primary: bool = False
    l4_bayes: bool = False
    l4_ml: bool = False
    l4_probability: bool = False

    # E10 Portfolio Construction feature flags (P0 defaults)
    e10_p0: bool = True
    e10_optimizer: bool = False
    e10_hrp: bool = False
    e10_mvo: bool = False

    # E13 Equity Fundamental L/S feature flags (P0 defaults)
    e13_p0: bool = True
    e13_revisions: bool = False
    e13_moat: bool = False
    e13_ml: bool = False

    # E08 Volatility & Options Intelligence feature flags (P0 defaults)
    e08_p0: bool = True
    e08_gamma: bool = False
    e08_dealer: bool = False
    e08_surface: bool = False
    e08_ml: bool = False

    # E09 CTA Trend Engine feature flags (P0 defaults)
    e09_p0: bool = True
    e09_breakout: bool = False
    e09_cross_asset: bool = False
    e09_ml: bool = False

    # E04 Statistical Arbitrage & Relative Value feature flags (P0 defaults)
    e04_p0: bool = True
    e04_kalman: bool = False
    e04_dynamic_hedge: bool = False
    e04_etf_basis: bool = False
    e04_ml: bool = False

    # E05 Event-Driven & Special Situations feature flags (P0 defaults)
    e05_p0: bool = True
    e05_deal_probability: bool = False
    e05_transcripts: bool = False
    e05_ml: bool = False

    # E11 Sentiment & Alternative Data feature flags (P0 defaults)
    e11_p0: bool = True
    e11_social: bool = False
    e11_transcripts: bool = False
    e11_llm: bool = False
    e11_ml: bool = False
    e11_altdata: bool = False

    # Validation & Backtesting platform flags (P0 defaults)
    backtest: bool = True
    live: bool = False

    # Continuous Research Evaluation platform flags (P0 defaults)
    cre: bool = True
    promotion: bool = False

    # Knowledge Intelligence Platform flags (P0 defaults)
    kip: bool = True
    kip_rag: bool = True
    kip_graph: bool = True
    kip_versioning: bool = True
    kip_ocr: bool = True
    kip_llm_summary: bool = True
    # KIP P1 — Continuous Knowledge Acquisition & House Intelligence
    kip_auto_ingest: bool = True
    kip_house_view: bool = True
    kip_prediction_tracking: bool = True
    kip_timeline: bool = True

    # Reasoning & Research Synthesis Platform flags (P0 defaults)
    rsp: bool = True
    rsp_consensus: bool = True
    rsp_contradictions: bool = True
    rsp_reasoning: bool = True

    # Research Management System flags (P0 defaults)
    rms: bool = True
    rms_review: bool = True
    rms_approval: bool = True
    rms_publish: bool = True

    # AGI Analyst Workspace flags (P0 defaults)
    aws: bool = True
    aws_copilot: bool = True
    aws_replay: bool = True
    aws_cre: bool = True

    # Investment Operations Centre flags (P0 defaults)
    ioc: bool = True
    ioc_alerts: bool = True
    ioc_reports: bool = True

    # Alpha Improvement Programme flags (research programme; not a platform)
    aip: bool = True
    aip_experiments: bool = True
    aip_promotion: bool = False

    # UI Aggregation Layer (client facade; not a platform redesign)
    ui: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
