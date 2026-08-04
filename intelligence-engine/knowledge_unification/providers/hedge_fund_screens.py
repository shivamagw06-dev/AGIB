"""Hedge fund screen provider — which institutional strategies flag a company today.

The hedge fund terminal already scans the covered universe every time it is
opened. This exposes the same result to Ask, so "why is X in the value
screen?" is answered from the scanner itself rather than re-derived.
"""

from __future__ import annotations

import time
from typing import Any

from knowledge_unification.providers.base import empty_result, error_result, timed_result
from knowledge_unification.schema import ProviderResult, ProviderSpec, QueryPlan


class HedgeFundScreenProvider:
    spec = ProviderSpec(
        id="hedge_fund_screens",
        label="Hedge fund strategy screens",
        coverage="Eight institutional screens across the covered Indian universe, refreshed per scan",
        priority=26,
        supported_question_types=("investment", "valuation", "company", "market", "portfolio"),
        typical_latency_ms=400,
        confidence_ceiling=0.8,
    )

    def health_check(self) -> str:
        try:
            from valuation_terminal.store import all_rows

            return "ok" if len(all_rows() or {}) >= 500 else "degraded"
        except Exception:
            return "error"

    def consult(self, plan: QueryPlan) -> ProviderResult:
        t0 = time.perf_counter()
        try:
            from hedge_fund_lab.terminal import opportunity

            ticker = plan.ticker_hint
            if not ticker:
                return empty_result(self.spec.id, t0, "no_screen_company")

            data = opportunity(ticker)
            if not data.get("ok"):
                return empty_result(self.spec.id, t0, data.get("error") or "not_scanned")

            matched = data.get("strategies_matched") or []
            name = data.get("company_name") or ticker
            if not matched:
                return empty_result(self.spec.id, t0, "no_screen_match")

            labels = [m.get("label") for m in matched if m.get("label")]
            summary = (
                f"{name} currently satisfies {len(matched)} institutional "
                f"{'screen' if len(matched) == 1 else 'screens'}: {', '.join(labels)}. "
                "Screen membership marks a research priority, not a position."
            )

            why: list[str] = [m.get("why") for m in matched if m.get("why")]
            for risk in (data.get("risks") or [])[:2]:
                why.append(f"Risk: {risk}")
            for catalyst in (data.get("catalysts") or [])[:2]:
                why.append(f"Catalyst: {catalyst}")

            facts: list[dict[str, Any]] = [
                {"field": f"screen_{m.get('strategy')}", "value": m.get("confidence"), "label": m.get("label")}
                for m in matched
            ]
            context = data.get("industry_context") or {}
            if context.get("gap_pct") is not None:
                facts.append({"field": "gap_to_industry_pct", "value": context.get("gap_pct")})

            return timed_result(
                self.spec.id,
                ok=True,
                empty=False,
                confidence=0.72,
                t0=t0,
                summary=summary,
                why=why,
                evidence=[{"source": "hedge_fund_lab.terminal", "title": f"screens:{ticker}"}],
                facts=facts,
                raw={
                    "ticker": ticker,
                    "company_name": name,
                    "strategies_matched": matched,
                    "calculation_chain": data.get("calculation_chain"),
                    "timeline": (data.get("timeline") or [])[-5:],
                },
            )
        except Exception as exc:
            return error_result(self.spec.id, t0, exc)
