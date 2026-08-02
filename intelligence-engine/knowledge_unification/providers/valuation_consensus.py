"""KUL provider — Capital IQ market consensus from valuation_consensus store.

Surfaces broker consensus / targets / coverage as Market Consensus observations
so Ask AGI can learn from the Valuation Intelligence dashboard.

Never frames CapIQ broker counts as AGI BUY/SELL recommendations.
AGI Institutional Intelligence remains a separate layer.
"""

from __future__ import annotations

import time
from typing import Any

from knowledge_unification.providers.base import empty_result, error_result, timed_result
from knowledge_unification.schema import ProviderResult, ProviderSpec, QueryPlan


class ValuationConsensusProvider:
    spec = ProviderSpec(
        id="valuation_consensus",
        label="Valuation Consensus (Capital IQ Market Consensus)",
        coverage="Institutional consensus dashboard — CapIQ targets, upside, broker counts, coverage",
        priority=18,
        supported_question_types=("company", "valuation", "market", "business_model"),
        typical_latency_ms=10,
        confidence_ceiling=0.9,
    )

    def health_check(self) -> str:
        try:
            from valuation_consensus.store import load_live

            n = int(load_live().get("row_count") or 0)
            if n >= 1000:
                return "ok"
            if n > 0:
                return "degraded"
            return "empty"
        except Exception:
            return "error"

    def consult(self, plan: QueryPlan) -> ProviderResult:
        t0 = time.perf_counter()
        try:
            from valuation_consensus.agi_panel import soft_consensus_facts
            from valuation_consensus.store import get_row

            ticker = plan.ticker_hint
            if not ticker:
                return empty_result(self.spec.id, t0, "no_ticker")

            row = get_row(ticker)
            if not row:
                return empty_result(self.spec.id, t0, "no_consensus_row")

            facts = soft_consensus_facts(row)
            if not facts:
                return empty_result(self.spec.id, t0, "no_usable_consensus_fields")

            name = row.get("company_name") or ticker
            why: list[str] = [
                "Market Consensus (Capital IQ) — distinct from AGI Institutional Intelligence."
            ]
            if row.get("target_price") is not None:
                why.append(
                    f"Consensus target for {name}: {row.get('target_price')} "
                    f"(CMP {row.get('cmp')}; upside {row.get('upside')}%)."
                )
            if row.get("coverage") is not None:
                why.append(f"Analyst coverage count: {row.get('coverage')}.")
            reco_bits = []
            for label, key in (
                ("Buy", "buy_count"),
                ("Outperform", "outperform_count"),
                ("Hold", "hold_count"),
                ("Sell", "sell_count"),
            ):
                if row.get(key) is not None:
                    reco_bits.append(f"{label} {row.get(key)}")
            if reco_bits:
                why.append(
                    "Broker recommendation counts (market consensus, not AGI advice): "
                    + "; ".join(reco_bits)
                    + "."
                )
            if row.get("sector") or row.get("industry"):
                why.append(
                    f"Sector/Industry: {row.get('sector') or 'n/a'} / {row.get('industry') or 'n/a'}."
                )

            summary = (
                f"{name} market consensus from Capital IQ"
                + (
                    f": target {row.get('target_price')}, upside {row.get('upside')}%."
                    if row.get("target_price") is not None
                    else f" ({row.get('sector') or 'listed'})."
                )
            )

            return timed_result(
                self.spec.id,
                ok=True,
                empty=False,
                confidence=0.87,
                t0=t0,
                summary=summary,
                why=why,
                evidence=[
                    {
                        "source": "valuation_consensus",
                        "title": f"{ticker}.market_consensus",
                        "effective_date": row.get("updated_at"),
                        "layer": "market_consensus",
                    }
                ],
                facts=facts,
                raw={
                    "ticker": ticker,
                    "layer": "market_consensus",
                    "provider_note": "CapIQ market consensus — not AGI recommendation",
                    "valuation": {
                        "cmp": row.get("cmp"),
                        "target_price": row.get("target_price"),
                        "target_high": row.get("target_high"),
                        "target_low": row.get("target_low"),
                        "upside": row.get("upside"),
                        "coverage": row.get("coverage"),
                        "buy_count": row.get("buy_count"),
                        "hold_count": row.get("hold_count"),
                        "sell_count": row.get("sell_count"),
                    },
                    "identity": {
                        "company_name": name,
                        "sector": row.get("sector"),
                        "industry": row.get("industry"),
                    },
                },
            )
        except Exception as exc:
            return error_result(self.spec.id, t0, exc)
