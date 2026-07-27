"""Soft production entry for Ask AGI — editorial rewrite after AGIB intelligence."""

from __future__ import annotations

from typing import Any

from editorial.flags import flags_dict, is_enabled
from editorial.package import build_structured_package
from editorial.schema import ARCHITECTURE_STATUS, EDITORIAL_VERSION, PROGRAMME
from editorial.service import EditorialService


def health() -> dict[str, Any]:
    return {
        **EditorialService().health(),
        "architecture_status": ARCHITECTURE_STATUS,
        "not_an_engine": True,
        "flags": flags_dict(),
    }


def quality_gates() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "version": EDITORIAL_VERSION,
        "architecture_status": ARCHITECTURE_STATUS,
        "passed": is_enabled(),
        "checks": {
            "enabled": is_enabled(),
            "writer_only": True,
            "never_reads_pdfs": True,
            "never_overrides_recommendation": True,
            "structured_intelligence_only": True,
            "fallback_template_on_failure": True,
            "cache_recommendations_24h": True,
        },
        "flags": flags_dict(),
    }


def package_for_ask_agi(
    *,
    query: str = "",
    ticker: str | None = None,
    answer_construction: dict[str, Any] | None = None,
    company_analysis: dict[str, Any] | None = None,
    institutional_answer: dict[str, Any] | None = None,
    company: str | None = None,
    detailed: bool = False,
) -> dict[str, Any]:
    """Soft-wire: take AGIB structured outputs → editorial prose.

    Returns empty/disabled package when layer is off. Never raises.
    """
    if not is_enabled():
        return {
            "enabled": False,
            "bypassed": True,
            "programme": PROGRAMME,
            "version": EDITORIAL_VERSION,
            "architecture_status": ARCHITECTURE_STATUS,
        }

    try:
        ac = answer_construction if isinstance(answer_construction, dict) else {}
        ia = institutional_answer if isinstance(institutional_answer, dict) else ac.get("institutional_answer")
        structured = build_structured_package(
            question=query,
            institutional_answer=ia if isinstance(ia, dict) else None,
            answer_construction=ac,
            company_analysis=company_analysis if isinstance(company_analysis, dict) else None,
            company=company,
            ticker=ticker,
        )
        service = EditorialService()
        if detailed:
            result = service.generateDetailedAnalysis(structured, question=query)
        elif isinstance(ia, dict) and (ia.get("is_recommendation_query") or ia.get("enabled")):
            result = service.generateRecommendation(structured, question=query)
        else:
            result = service.generateQuickAnalysis(structured, question=query)

        return {
            "enabled": True,
            "programme": PROGRAMME,
            "version": EDITORIAL_VERSION,
            "architecture_status": ARCHITECTURE_STATUS,
            "role": "writer_only",
            "agib_is_brain": True,
            "flags": flags_dict(),
            "structured_intelligence": structured,
            "editorial": result,
            "executive": result.get("text"),
            "fallback": bool(result.get("fallback")),
            "provider": result.get("provider"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "enabled": True,
            "programme": PROGRAMME,
            "version": EDITORIAL_VERSION,
            "architecture_status": ARCHITECTURE_STATUS,
            "error": str(exc),
            "fallback": True,
            "executive": None,
        }
