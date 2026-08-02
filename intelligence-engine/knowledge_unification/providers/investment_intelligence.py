"""Investment Intelligence provider — Phase 3.2.5 KUL integration.

Wraps investment_intelligence.production.analyse. Surfaces thesis, quality,
catalysts, risks, scenarios, valuation drivers, evidence, and monitoring —
without BUY/SELL recommendations. Does not bypass KUL.
"""

from __future__ import annotations

import time
from typing import Any

from knowledge_unification.providers.base import empty_result, error_result, timed_result
from knowledge_unification.schema import ProviderResult, ProviderSpec, QueryPlan

_INV_TYPES = frozenset(
    {
        "investment",
        "company",
        "business_model",
        "business_risk",
        "comparison",
        "valuation",
        "moat",
    }
)


class InvestmentIntelligenceProvider:
    spec = ProviderSpec(
        id="investment_intelligence",
        label="Investment Intelligence Engine",
        coverage=(
            "Deterministic investment thesis, quality, catalysts, risks, scenarios, "
            "valuation drivers, evidence, monitoring — observations only (no BUY/SELL)"
        ),
        priority=6,
        supported_question_types=(
            "investment",
            "company",
            "business_model",
            "business_risk",
            "comparison",
            "valuation",
            "moat",
        ),
        typical_latency_ms=45,
        confidence_ceiling=0.93,
    )

    def health_check(self) -> str:
        try:
            from investment_intelligence.production import health

            h = health()
            return "ok" if h.get("ok") is not False else "degraded"
        except Exception:
            return "error"

    def consult(self, plan: QueryPlan) -> ProviderResult:
        t0 = time.perf_counter()
        types = set(plan.question_types or [])
        q = (plan.question or "").lower()

        # Skip pure industry pedagogy / accounting / macro unless investment-shaped.
        investment_shaped = "investment" in types or any(
            k in q
            for k in (
                "investment thesis",
                "catalyst",
                "scenario",
                "investors monitor",
                "evidence strength",
                "investment quality",
                "investment risk",
                "from an investment",
                "committee",
                "attractive",
                "downside risk",
            )
        )
        if types and not types.intersection(_INV_TYPES) and not investment_shaped:
            return empty_result(self.spec.id, t0, "not_investment_shaped")

        # Pure industry DNA pedagogy without company / investment verbs → leave to II.
        if (
            not investment_shaped
            and "industry" in types
            and "company" not in types
            and not plan.ticker_hint
            and not plan.company_hint
            and "comparison" not in types
        ):
            return empty_result(self.spec.id, t0, "industry_pedagogy_defer_to_ii")

        try:
            from investment_intelligence.production import analyse

            out = analyse(plan.question) or {}
        except Exception as exc:
            return error_result(self.spec.id, t0, exc)

        try:
            summary = str(out.get("executive_summary") or out.get("summary") or "").strip()
            if not out.get("ok") or not summary:
                return empty_result(self.spec.id, t0, "inv_empty")
            if summary.lower().startswith("investment intelligence needs a supported"):
                return empty_result(self.spec.id, t0, "inv_unresolved_entity")

            # Hard policy: never surface recommendation leakage via KUL.
            if out.get("recommendation") not in (None, "", "none", "NONE"):
                return empty_result(self.spec.id, t0, "inv_recommendation_blocked")

            modules = list(out.get("modules_used") or [])
            why = [str(w) for w in (out.get("supporting_analysis") or []) if w][:8]
            if out.get("entity"):
                why.insert(0, f"Investment Intelligence entity: {out.get('entity')}.")
            if not why and modules:
                why.append("INV modules: " + ", ".join(modules[:6]) + ".")
            why.append("Observations only — no BUY/SELL recommendation.")

            evidence = [
                {
                    "source": "investment_intelligence",
                    "title": "modules:" + ",".join(modules[:6]) if modules else "inv_analyse",
                    "entity": out.get("entity"),
                    "recommendation_policy": out.get("recommendation_policy"),
                }
            ]

            facts: list[dict[str, Any]] = [
                {"field": "modules_used", "value": modules},
                {"field": "entity", "value": out.get("entity")},
                {"field": "industry", "value": out.get("industry")},
                {"field": "recommendation_policy", "value": out.get("recommendation_policy")},
                {"field": "recommendation", "value": None},
            ]
            ql = out.get("quality") or {}
            if isinstance(ql, dict) and ql.get("composite_score") is not None:
                facts.append({"field": "quality_composite", "value": ql.get("composite_score")})
            if out.get("unknowns"):
                facts.append({"field": "unknowns", "value": list(out.get("unknowns") or [])[:6]})
            if out.get("monitoring_points"):
                facts.append(
                    {"field": "monitoring_points", "value": list(out.get("monitoring_points") or [])[:6]}
                )

            conf = float(out.get("confidence") or 0.8)
            conf = min(conf, self.spec.confidence_ceiling)

            return timed_result(
                self.spec.id,
                ok=True,
                empty=False,
                confidence=conf,
                t0=t0,
                summary=summary[:900],
                why=why,
                evidence=evidence,
                facts=[f for f in facts if f.get("value") is not None or f.get("field") == "recommendation"],
                raw=out,
            )
        except Exception as exc:
            return error_result(self.spec.id, t0, exc)
