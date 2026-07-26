"""FDI production facade — soft layer, no redesign."""

from __future__ import annotations

from typing import Any

from filing_diff.flags import flags_dict, is_enabled
from filing_diff.pipeline import analyse_diff
from filing_diff.schema import FDI_VERSION


def dashboard() -> dict[str, Any]:
    return {
        "programme": "AGIB_FILING_DIFF_ENGINE",
        "fdi_version": FDI_VERSION,
        "enabled": is_enabled(),
        "architecture_status": "v1.0.1 LOCKED",
        "primary_question": "What materially changed since the previous filing?",
        "flags": flags_dict(),
        "pipeline": [
            "Official Filings",
            "FIL",
            "FDI",
            "EIL",
            "PIL",
            "Institutional Analysts",
            "Investment Committee",
            "CIO",
            "Research Writer",
            "ACS",
            "IRS",
            "Production",
        ],
        "no_redesign": [
            "engine",
            "ui",
            "provider",
            "filing_intelligence",
            "evidence_intelligence",
            "peer_intelligence",
            "company_analysis",
            "investment_committee",
            "cio",
            "research_writer",
            "certification",
            "regression",
        ],
    }


def company(ticker: str) -> dict[str, Any]:
    if not is_enabled():
        return {"enabled": False, "fdi_version": FDI_VERSION}
    out = analyse_diff(ticker)
    return {"enabled": True, **out}


def analyse(ticker: str) -> dict[str, Any]:
    return company(ticker)


def timeline(ticker: str) -> dict[str, Any]:
    out = analyse_diff(ticker)
    return {
        "enabled": is_enabled(),
        "fdi_version": FDI_VERSION,
        "ticker": out.get("ticker") or ticker,
        "found": out.get("found"),
        "timeline": out.get("timeline") or [],
        "comparison": out.get("comparison"),
    }


def changes(ticker: str) -> dict[str, Any]:
    out = analyse_diff(ticker)
    return {
        "enabled": is_enabled(),
        "fdi_version": FDI_VERSION,
        "ticker": out.get("ticker") or ticker,
        "found": out.get("found"),
        "changes": out.get("changes") or [],
        "confidence": out.get("confidence"),
    }


def soft_slice_for_fil(ticker: str | None = None) -> dict[str, Any]:
    if not is_enabled():
        return {}
    if ticker:
        out = analyse_diff(ticker)
        return {
            "filing_diff": {
                "enabled": True,
                "version": FDI_VERSION,
                "found": out.get("found"),
                "comparison": out.get("comparison"),
                "material_count": len(out.get("changes") or []),
                "cio_brief": (out.get("report") or {}).get("cio_brief"),
            }
        }
    return {
        "filing_diff": {
            "enabled": True,
            "version": FDI_VERSION,
            "rule": "Every new filing must generate a Filing Diff Report",
        }
    }


def soft_slice_for_irs() -> dict[str, Any]:
    if not is_enabled():
        return {}
    return {
        "filing_diff": {
            "enabled": True,
            "version": FDI_VERSION,
            "quality_gates_passed": quality_gates().get("passed"),
            "rule": "New risks/guidance/financial/management/capital changes must be detected with evidence",
        }
    }


def soft_slice_for_analyst(ticker: str, *, analyst: str = "committee") -> dict[str, Any]:
    if not is_enabled():
        return {}
    out = analyse_diff(ticker)
    if not out.get("found"):
        return {"filing_diff": {"enabled": True, "found": False, "ticker": ticker}}
    report = out.get("report") or {}
    payload = {
        "enabled": True,
        "version": FDI_VERSION,
        "ticker": out["ticker"],
        "comparison": out.get("comparison"),
        "cio_brief": report.get("cio_brief"),
        "top_changes": report.get("top_10_material_changes") or [],
        "thesis_impact": report.get("investment_thesis_impact"),
        "rule": "Deliver what changed — not a latest-filing summary; never Buy/Sell",
    }
    if analyst in {"committee", "cio"}:
        payload["committee"] = report.get("committee")
    if analyst == "research_writer":
        payload["writer_blocks"] = {
            "qoq": out.get("comparison"),
            "financial": report.get("financial_changes"),
            "management": report.get("management_changes"),
            "risks": report.get("risk_changes"),
            "guidance": report.get("guidance_changes"),
            "capital": report.get("capital_allocation_changes"),
        }
    return {"filing_diff": payload}


def quality_gates() -> dict[str, Any]:
    out = analyse_diff("HDFCBANK")
    changes = out.get("changes") or []
    domains = {c.get("domain") for c in changes}
    evidence = out.get("evidence") or {}
    cosmetic_flagged = [
        c for c in (out.get("all_detected") or [])
        if c.get("cosmetic") and c.get("materiality") not in {"ignore", None}
    ]
    checks = {
        "enabled": is_enabled(),
        "hdfc_found": bool(out.get("found")),
        "financial_changes_detected": any(c.get("domain") == "statement" for c in changes),
        "guidance_changes_detected": any(c.get("domain") == "guidance" for c in changes),
        "management_changes_detected": any(c.get("domain") == "management" for c in changes),
        "risk_or_capital_detected": bool(domains & {"risks", "capital"}),
        "material_changes_have_evidence": (evidence.get("linked_count") or 0) >= 1,
        "no_cosmetic_as_material": len(cosmetic_flagged) == 0,
        "thesis_impact_present": bool((out.get("report") or {}).get("investment_thesis_impact")),
        "no_buy_sell": not any(
            phrase in ((out.get("report") or {}).get("text") or "").lower()
            for phrase in ("buy rating", "sell rating", "recommendation: buy", "recommendation: sell")
        ),
        "flags": flags_dict().get("FILING_DIFF_ENGINE") is True,
    }
    return {"passed": all(checks.values()), "checks": checks, "fdi_version": FDI_VERSION}


def admin_page() -> str:
    dash = dashboard()
    gates = quality_gates()
    out = analyse_diff("HDFCBANK")
    report = out.get("report") or {}
    rows = "".join(
        f"<tr><td>{c.get('materiality')}</td><td>{c.get('domain')}</td>"
        f"<td>{c.get('metric')}</td><td>{c.get('change_type')}</td>"
        f"<td>{c.get('previous_value')} → {c.get('current_value')}</td>"
        f"<td>{c.get('thesis_impact')}</td></tr>"
        for c in (report.get("top_10_material_changes") or [])[:10]
    )
    return f"""<!doctype html>
<html><head><title>FDI — Filing Diff</title>
<style>
body{{font-family:Georgia,serif;background:#0f1419;color:#e7ecf1;margin:2rem}}
h1{{letter-spacing:.04em}} .card{{border:1px solid #2a3440;padding:1rem 1.25rem;margin:1rem 0}}
table{{border-collapse:collapse;width:100%}} td,th{{border-bottom:1px solid #2a3440;padding:.4rem;text-align:left;font-size:0.92rem}}
.ok{{color:#7dcea0}} .bad{{color:#f5b7b1}}
</style></head><body>
<h1>Filing Diff Engine</h1>
<p>Primary question: <em>What materially changed since the previous filing?</em></p>
<div class="card">
  <div>Version: {dash.get('fdi_version')}</div>
  <div>Compare: {out.get('previous_period')} → {out.get('current_period')}</div>
  <div class="{'ok' if gates.get('passed') else 'bad'}">Quality gates: {'PASSED' if gates.get('passed') else 'FAILED'}</div>
</div>
<div class="card"><h2>CIO brief</h2><p>{report.get('cio_brief')}</p></div>
<div class="card"><h2>Top material changes</h2>
<table><tr><th>Mat</th><th>Domain</th><th>Metric</th><th>Type</th><th>Prev→Cur</th><th>Thesis</th></tr>{rows}</table>
</div>
<p>API: /v1/filing-diff/* · Flag: FILING_DIFF_ENGINE</p>
</body></html>"""
