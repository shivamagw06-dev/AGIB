"""Capital IQ → warehouse import framework (via IKT / refresh stage).

Does not download vendor historical PE/PB/EV. Statement / consensus / master
rows are staged through the existing institutional_warehouse refresh path and
IKT CapIQ tables.
"""

from __future__ import annotations

from typing import Any, Optional

from financial_warehouse_completion.models import ENGINE_CODE, PROGRAMME_VERSION


def import_framework_status() -> dict[str, Any]:
    """Describe CapIQ import readiness without calling live vendors."""
    ikt_ok = False
    ikt_tables: list[str] = []
    try:
        from institutional_knowledge_tables import production as ikt

        health = ikt.health() if hasattr(ikt, "health") else {}
        ikt_ok = bool(health.get("ok", True))
        # Best-effort table listing
        if hasattr(ikt, "list_tables"):
            ikt_tables = list(ikt.list_tables() or [])[:40]
    except Exception as exc:
        return {
            "ok": False,
            "source": "capital_iq",
            "ikt_ready": False,
            "error": str(exc)[:200],
            "engine": ENGINE_CODE,
            "version": PROGRAMME_VERSION,
            "imports": ["company_master", "financials_annual", "consensus"],
            "never": ["historical_pe", "historical_pb", "historical_ev_ebitda"],
        }
    return {
        "ok": True,
        "source": "capital_iq",
        "ikt_ready": ikt_ok,
        "ikt_tables_sample": ikt_tables,
        "pipeline_stage": "capital_iq",
        "imports": ["company_master", "financials_annual", "consensus", "ownership"],
        "normalisation": {
            "currency": "INR preferred",
            "units": "INR million via warehouse units.normalise_rows",
            "statement_preference": "CONSOLIDATED > STANDALONE",
        },
        "never": ["historical_pe", "historical_pb", "historical_ev_ebitda"],
        "engine": ENGINE_CODE,
        "version": PROGRAMME_VERSION,
    }


def run_capital_iq_stage(
    *,
    limit: Optional[int] = None,
    actor: str = "fwcp",
) -> dict[str, Any]:
    """Execute the warehouse CapIQ refresh stage (IKT → warehouse)."""
    try:
        from institutional_warehouse.refresh import stage_capital_iq
    except Exception as exc:
        return {"ok": False, "error": f"stage_unavailable:{exc}", "engine": ENGINE_CODE}

    try:
        # stage_capital_iq signatures vary — support common kwargs.
        try:
            out = stage_capital_iq(limit=limit, actor=actor)
        except TypeError:
            out = stage_capital_iq()
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:240], "engine": ENGINE_CODE, "version": PROGRAMME_VERSION}

    return {
        "ok": bool((out or {}).get("ok", True)),
        "stage": "capital_iq",
        "result": out,
        "engine": ENGINE_CODE,
        "version": PROGRAMME_VERSION,
        "vendor_historical_multiples": False,
    }
