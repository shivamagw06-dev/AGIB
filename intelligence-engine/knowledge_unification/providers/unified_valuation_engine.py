"""KUL provider — Unified Valuation Engine (UVE)."""

from __future__ import annotations

import time

from knowledge_unification.providers.base import empty_result, timed_result
from knowledge_unification.schema import ProviderResult, ProviderSpec, QueryPlan

_MARKERS = (
    "valuation",
    "expensive",
    "cheap",
    "overvalued",
    "undervalued",
    "multiple",
    "p/e",
    "pe ",
    "p/b",
    "ev/ebitda",
    "fairly valued",
    "relative to",
    "peer",
    "sector",
    "industry",
    "compare",
    "institutional",
    "premium",
    "discount",
    "analyze",
    "outlook",
    "compounder",
    "roce",
)


class UnifiedValuationEngineProvider:
    spec = ProviderSpec(
        id="unified_valuation_engine",
        label="Unified Valuation Engine",
        coverage=(
            "Warehouse + Upstox + VPAE-gated company valuation packs — "
            "no vendors at Ask time, no BUY/SELL"
        ),
        priority=7,
        supported_question_types=(
            "valuation", "company", "investment", "comparison", "market", "screen",
        ),
        typical_latency_ms=180,
        confidence_ceiling=0.9,
    )

    def health_check(self) -> str:
        try:
            from valuation_engine.service import get_company_valuation  # noqa: F401

            return "ok"
        except Exception:
            return "degraded"

    def consult(self, plan: QueryPlan) -> ProviderResult:
        t0 = time.perf_counter()
        qlow = (plan.question or "").lower()
        if not any(m in qlow for m in _MARKERS):
            return empty_result(self.spec.id, t0, "not_a_valuation_question")
        ticker = (plan.ticker_hint or "").strip().upper()
        if not ticker:
            return empty_result(self.spec.id, t0, "no_company_for_uve")
        try:
            from valuation_engine.service import get_company_valuation

            pack = get_company_valuation(ticker)
        except Exception as exc:
            return empty_result(self.spec.id, t0, str(exc)[:160])
        if not pack.get("ok"):
            return empty_result(self.spec.id, t0, str(pack.get("error") or "uve_empty"))

        primary = pack.get("primary_metric") or pack.get("primary_model") or "pe"
        lens = pack.get("lens") or {}
        summary = (
            f"{ticker} valuation pack via UVE — primary metric {str(primary).upper()}"
            + (f" ({lens.get('primary_metric_label')})" if lens.get("primary_metric_label") else "")
            + ". Policy-gated multiples from warehouse / Upstox; no price target."
        )
        why = []
        for key in ("pe", "pb", "ev_ebitda", "roe"):
            block = (pack.get("metrics") or {}).get(key) or pack.get(key)
            if isinstance(block, dict) and block.get("value") is not None:
                why.append(f"{key.upper()}={block.get('value')} ({block.get('status') or 'observed'})")
            elif block is not None and not isinstance(block, dict):
                why.append(f"{key.upper()}={block}")
        if pack.get("policy_status"):
            why.append(f"VPAE status: {pack.get('policy_status')}")
        try:
            from valuation_engine.prompt import OUTPUT_SECTIONS, UVE_PROMPT_VERSION

            prompt_meta = {
                "id": "uve_institutional_system_prompt_v3",
                "version": UVE_PROMPT_VERSION,
                "sections": list(OUTPUT_SECTIONS),
            }
        except Exception:
            prompt_meta = {"id": "uve_institutional_system_prompt_v3", "version": "v3.0.0", "sections": []}
        return timed_result(
            self.spec.id,
            ok=True,
            empty=False,
            confidence=0.78,
            t0=t0,
            summary=summary,
            why=why[:8],
            evidence=[{"source": "unified_valuation_engine", "title": f"uve:{ticker}"}],
            facts=[
                {"field": "primary_metric", "value": primary, "source": "uve"},
                {"field": "policy_status", "value": pack.get("policy_status"), "source": "vpae"},
            ],
            raw={"engine": "unified_valuation_engine", "pack": {
                "primary_metric": primary,
                "policy_status": pack.get("policy_status"),
                "metrics": pack.get("metrics"),
            }, "prompt": prompt_meta},
        )
