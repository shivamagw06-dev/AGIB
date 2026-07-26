"""CAE configuration — intents, engine policies, token budgets."""

from __future__ import annotations

INTENT_LABELS: list[str] = [
    "company_research",
    "sector_research",
    "macro_analysis",
    "portfolio_question",
    "forecast",
    "risk",
    "event",
    "comparison",
    "valuation",
    "investment_thesis",
    "news",
    "monitoring",
    "education",
    "market_overview",
    "mixed_intent",
]

# Intent → engines to retrieve from (dynamic retrieval policy)
INTENT_ENGINES: dict[str, list[str]] = {
    "company_research": ["mee", "fle", "iie", "eve", "aoi", "kc", "kf"],
    "sector_research": ["mee", "iie", "fle", "eve", "kf", "kc"],
    "macro_analysis": ["mee", "fle", "eve", "aoi", "kf"],
    "portfolio_question": ["fle", "mee", "iie", "eve", "kf"],
    "forecast": ["fle", "iie", "mee", "eve", "kf"],
    "risk": ["iie", "mee", "fle", "eve", "kf"],
    "event": ["mee", "eve", "iie", "fle", "aoi"],
    "comparison": ["iie", "fle", "eve", "mee", "kf"],
    "valuation": ["iie", "fle", "eve", "kf", "kc"],
    "investment_thesis": ["iie", "eve", "fle", "mee", "kf", "kc"],
    "news": ["mee", "aoi", "eve", "iie"],
    "monitoring": ["mee", "fle", "iie", "eve"],
    "education": ["kf", "kc", "iie"],
    "market_overview": ["mee", "aoi", "fle", "kf"],
    "mixed_intent": ["mee", "fle", "iie", "eve", "aoi", "kc", "kf"],
}

INTENT_KEYWORDS: dict[str, list[str]] = {
    "company_research": ["buy", "sell", "hold", "stock", "company", "ticker", "share"],
    "sector_research": ["sector", "industry", "banking", "it services", "pharma", "auto"],
    "macro_analysis": ["macro", "gdp", "inflation", "repo", "rbi", "oil", "usd", "fiscal"],
    "portfolio_question": ["portfolio", "allocation", "position", "exposure", "holding"],
    "forecast": ["forecast", "predict", "outlook", "guidance", "expect", "target"],
    "risk": ["risk", "downside", "bear", "threat", "litigation", "downgrade"],
    "event": ["event", "what changed", "announcement", "news", "happened"],
    "comparison": ["compare", "versus", "vs", "better than", "relative"],
    "valuation": ["valuation", "cheap", "expensive", "multiple", "pe ", "dcf"],
    "investment_thesis": ["thesis", "why own", "investment case", "bull case", "bear case"],
    "news": ["latest", "today", "breaking", "headline"],
    "monitoring": ["monitor", "watch", "track", "checklist", "alert"],
    "education": ["what is", "explain", "how does", "define", "meaning"],
    "market_overview": ["market", "nifty", "sensex", "indices", "breadth"],
}

PRIORITY_ORDER: list[str] = ["critical", "important", "optional"]

# Soft token budgets (approx chars/4 ≈ tokens; we budget by item counts + char caps)
DEFAULT_TOKEN_BUDGET = 3500
CRITICAL_ITEM_CAP = 8
IMPORTANT_ITEM_CAP = 12
OPTIONAL_ITEM_CAP = 8
CRITICAL_CHAR_CAP = 4000
IMPORTANT_CHAR_CAP = 3000
OPTIONAL_CHAR_CAP = 1500

CACHE_TTL_SECONDS = 120
ENGINE_TIMEOUT_MS = 800

# Ranking weights
RANK_WEIGHTS: dict[str, float] = {
    "relevance": 0.28,
    "freshness": 0.16,
    "confidence": 0.18,
    "evidence_quality": 0.12,
    "forecast_accuracy": 0.08,
    "event_severity": 0.08,
    "source_trust": 0.05,
    "knowledge_quality": 0.05,
}
