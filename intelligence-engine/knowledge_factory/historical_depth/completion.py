"""Hard vs soft completion + knowledge density for institutional historical backfill.

Hard requirements gate maintenance eligibility.
Soft requirements never permanently block a company (e.g. missing 2011 transcripts).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from knowledge_factory.historical_depth import store as hd_store

TARGET_YEARS = float(os.getenv("KF_HD_TARGET_YEARS") or "15")

# Hard — company may enter maintenance only when these pass.
HARD_DIMS = (
    "ohlcv",
    "corporate_actions",
    "financial_statements",
    "shareholding",
    "embeddings",
    "qa",
)

# Soft — measured for richness; N/A or missing does not block maintenance forever.
SOFT_DIMS = (
    "investor_presentations",
    "earnings_transcripts",
    "ir_pdfs",
    "historical_news",
    "esg_reports",
)


def _years_from_prices(entity: str) -> float:
    prices = hd_store.get_series("prices", entity) or {}
    ends = [str(r.get("period_end") or "")[:10] for r in (prices.get("records") or []) if r.get("period_end")]
    if len(ends) < 2:
        return 0.0
    try:
        d0 = datetime.fromisoformat(min(ends))
        d1 = datetime.fromisoformat(max(ends))
        return max(0.0, (d1 - d0).days / 365.25)
    except Exception:
        return float(max(0, len({e[:4] for e in ends}) - 1))


def _annual_years(entity: str) -> float:
    annual = hd_store.get_series("financials_annual", entity) or {}
    return float(len(annual.get("records") or []))


def history_years(entity: str) -> float:
    return max(_years_from_prices(entity), _annual_years(entity))


def _effective_target(entity: str, target_years: float) -> float:
    """Cap target at listing span when company is newer than target."""
    prices = hd_store.get_series("prices", entity) or {}
    ends = [str(r.get("period_end") or "")[:10] for r in (prices.get("records") or []) if r.get("period_end")]
    if not ends:
        return target_years
    try:
        listed = datetime.fromisoformat(min(ends))
        span = max(
            0.5,
            (datetime.now(timezone.utc).replace(tzinfo=None) - listed.replace(tzinfo=None)).days / 365.25,
        )
        return min(target_years, max(span, 1.0))
    except Exception:
        return target_years


def _ir_docs(entity: str) -> list[dict[str, Any]]:
    try:
        from live_data import store as lidi_store

        row = lidi_store.get_object("company_ir", entity.upper()) or {}
        return list(row.get("documents") or [])
    except Exception:
        return []


def _has_extract(entity: str) -> bool:
    try:
        from continuous_gather_learn import persist as cgl_persist

        ex = cgl_persist.get_knowledge_extract(entity)
        return bool(ex and (ex.get("metrics") or ex.get("kind")))
    except Exception:
        return False


def _has_embedding(entity: str) -> bool:
    try:
        from continuous_gather_learn import persist as cgl_persist

        emb = cgl_persist.get_embedding(entity)
        return bool(emb and emb.get("vector"))
    except Exception:
        return False


def _attempt_meta(entity: str) -> dict[str, Any]:
    return hd_store.get_report(f"backfill_attempts_{entity.upper()}") or {}


def record_attempt(entity: str, dimension: str, *, status: str, detail: str | None = None) -> None:
    e = entity.upper()
    meta = _attempt_meta(e)
    dims = dict(meta.get("dimensions") or {})
    dims[dimension] = {
        "status": status,
        "detail": (detail or "")[:200],
        "at": datetime.now(timezone.utc).isoformat(),
    }
    meta["dimensions"] = dims
    meta["entity"] = e
    hd_store.put_report(f"backfill_attempts_{e}", meta)


def _score(dims: dict[str, Any], keys: tuple[str, ...]) -> float:
    """Percent complete among keys. Soft N/A counts as complete for soft score."""
    if not keys:
        return 0.0
    ok = 0
    for k in keys:
        st = (dims.get(k) or {}).get("status")
        if st in {"complete", "n_a"}:
            ok += 1
    return round(100.0 * ok / len(keys), 2)


def knowledge_density(entity: str) -> dict[str, Any]:
    """How rich the intelligence is — not just whether the company was processed."""
    e = entity.upper()
    years = history_years(e)
    docs = _ir_docs(e)
    doc_n = len(docs)
    extracts_n = 0
    metrics_n = 0
    try:
        from continuous_gather_learn import persist as cgl_persist

        ex = cgl_persist.get_knowledge_extract(e) or {}
        if ex:
            extracts_n = 1
            metrics_n = len(ex.get("metrics") or {})
            # Approximate "facts" from themes/risks/catalysts + metrics
            extracts_n = metrics_n + len(ex.get("themes") or []) + len(ex.get("risks") or []) + len(
                ex.get("catalysts") or []
            )
        emb = cgl_persist.get_embedding(e) or {}
        emb_n = 1 if emb.get("vector") else 0
        # Scale embeddings notionally with vector dims presence; keep count simple
        if emb.get("vector"):
            emb_n = max(1, int(len(emb.get("vector") or []) // 4))
    except Exception:
        emb_n = 0

    annual_n = len((hd_store.get_series("financials_annual", e) or {}).get("records") or [])
    q_n = len((hd_store.get_series("financials_quarterly", e) or {}).get("records") or [])
    price_n = len((hd_store.get_series("prices", e) or {}).get("records") or [])
    action_n = len((hd_store.get_series("corporate_actions", e) or {}).get("records") or [])

    # Composite density score (0–100)
    score = 0.0
    score += min(30.0, years * 2.0)  # up to 30 for depth
    score += min(20.0, doc_n * 2.0)  # docs
    score += min(20.0, extracts_n * 1.5)  # extracts/facts
    score += min(15.0, emb_n * 2.0)  # embeddings
    score += min(15.0, (annual_n + q_n / 4.0 + min(price_n, 120) / 12.0 + action_n) * 0.5)

    if score >= 75:
        label = "Excellent"
    elif score >= 55:
        label = "Good"
    elif score >= 30:
        label = "Moderate"
    else:
        label = "Thin"

    return {
        "entity": e,
        "years": round(years, 2),
        "documents": doc_n,
        "extracts": extracts_n,
        "embeddings": emb_n,
        "financial_periods": annual_n + q_n,
        "price_points": price_n,
        "corporate_actions": action_n,
        "density_score": round(score, 1),
        "density": label,
    }


def evaluate_completion(entity: str, *, target_years: float | None = None) -> dict[str, Any]:
    """Per-dimension status with hard/soft/overall percentages."""
    e = entity.upper()
    target = float(target_years if target_years is not None else TARGET_YEARS)
    eff = _effective_target(e, target)
    years = history_years(e)
    attempts = (_attempt_meta(e).get("dimensions") or {})

    prices = hd_store.get_series("prices", e) or {}
    annual = hd_store.get_series("financials_annual", e) or {}
    quarterly = hd_store.get_series("financials_quarterly", e) or {}
    actions = hd_store.get_series("corporate_actions", e) or {}
    docs = _ir_docs(e)
    doc_types = {str(d.get("doc_type")) for d in docs}

    def _dim(ok: bool, *, n_a: bool = False, detail: str = "") -> dict[str, Any]:
        if ok:
            return {"status": "complete", "detail": detail}
        if n_a:
            return {"status": "n_a", "detail": detail}
        return {"status": "missing", "detail": detail}

    try:
        from live_data.qa import qa_price_points

        qa = qa_price_points(list(prices.get("records") or []))
        qa_ok = bool(qa.get("ok")) if prices.get("records") else False
    except Exception:
        qa_ok = bool(prices.get("records"))

    ohlcv_ok = years + 1e-9 >= eff and len(prices.get("records") or []) >= 12
    ca_n = len(actions.get("records") or [])
    ca_attempt = attempts.get("corporate_actions") or {}
    ca_ok = ca_n > 0 or ca_attempt.get("status") in {"complete", "empty", "n_a"}

    ann_n = len(annual.get("records") or [])
    q_n = len(quarterly.get("records") or [])
    annual_ok = ann_n >= max(3, int(min(eff, target))) or (ohlcv_ok and ann_n >= int(eff * 0.5))
    q_need = max(4, int(min(eff, target) * 4 * 0.5))
    quarterly_ok = q_n >= min(q_need, 8) or (eff < 2 and q_n >= 2)
    financials_ok = annual_ok and quarterly_ok

    # Shareholding — hard: present OR attempted empty/n_a (many names lack public history APIs yet)
    sh_series = hd_store.get_series("shareholding", e)
    sh_attempt = attempts.get("shareholding") or {}
    sh_ok = bool(sh_series and (sh_series.get("records") or [])) or sh_attempt.get("status") in {
        "complete",
        "empty",
        "n_a",
    }

    # Soft dims
    ip_ok = "investor_presentation" in doc_types
    tr_ok = "earnings_transcript" in doc_types
    ir_ok = "annual_report" in doc_types or any(
        t in doc_types for t in ("quarterly_results", "press_release", "other")
    )
    esg_ok = "esg_report" in doc_types
    news_ok = False
    try:
        from live_data import store as lidi_store

        snap = lidi_store.get_latest_snapshot("nse_announcements", "LATEST") or {}
        events = (snap.get("payload") or {}).get("events") or []
        news_ok = any(str(ev.get("symbol") or "").upper() == e for ev in events if isinstance(ev, dict))
    except Exception:
        news_ok = False
    if (attempts.get("historical_news") or attempts.get("announcements") or {}).get("status") in {
        "complete",
        "empty",
        "n_a",
    }:
        # Attempt recorded — soft N/A allowed
        news_na = not news_ok
    else:
        news_na = False

    def _soft_dim(present: bool, attempt_key: str) -> dict[str, Any]:
        att = attempts.get(attempt_key) or {}
        if present:
            return _dim(True)
        if att.get("status") in {"n_a", "empty", "complete"} or attempts.get("_wave"):
            return _dim(False, n_a=True, detail="unavailable_or_not_published")
        return _dim(False, detail="missing")

    dims = {
        "ohlcv": _dim(ohlcv_ok, detail=f"years={years:.2f} target={eff:.2f}"),
        "corporate_actions": _dim(ca_ok, n_a=ca_attempt.get("status") == "n_a", detail=f"n={ca_n}"),
        "financial_statements": _dim(
            financials_ok, detail=f"annual={ann_n} quarterly={q_n}"
        ),
        "shareholding": _dim(sh_ok, n_a=sh_attempt.get("status") == "n_a", detail="shareholding"),
        "embeddings": _dim(_has_embedding(e) and _has_extract(e)),
        "qa": _dim(qa_ok, detail="price_qa"),
        "investor_presentations": _soft_dim(ip_ok, "investor_presentations"),
        "earnings_transcripts": _soft_dim(tr_ok, "earnings_transcripts"),
        "ir_pdfs": _soft_dim(ir_ok, "annual_reports"),
        "historical_news": _dim(news_ok, n_a=news_na, detail="announcements_news"),
        "esg_reports": _soft_dim(esg_ok, "esg_reports"),
    }

    hard_pct = _score(dims, HARD_DIMS)
    soft_pct = _score(dims, SOFT_DIMS)
    overall_pct = round((hard_pct * 0.7 + soft_pct * 0.3), 2)

    # Hard gate: core dims must be complete; shareholding may be n_a after explicit attempt
    hard_ok = True
    for d in ("ohlcv", "corporate_actions", "financial_statements", "embeddings", "qa"):
        if dims[d]["status"] != "complete":
            hard_ok = False
            break
    if dims["shareholding"]["status"] not in {"complete", "n_a"}:
        hard_ok = False

    density = knowledge_density(e)

    return {
        "entity": e,
        "complete": hard_ok,  # maintenance eligibility = hard requirements
        "fully_backfilled": hard_ok,
        "hard_ok": hard_ok,
        "soft_ok": soft_pct >= 99.9,  # informational
        "hard_pct": hard_pct,
        "soft_pct": soft_pct,
        "overall_pct": overall_pct,
        "history_years": round(years, 2),
        "effective_target_years": round(eff, 2),
        "configured_target_years": target,
        "coverage_pct": overall_pct,
        "dimensions": dims,
        "hard_dimensions": HARD_DIMS,
        "soft_dimensions": SOFT_DIMS,
        "density": density,
        "mode": "maintenance" if hard_ok else "backfill",
    }


def company_scorecard(entity: str) -> dict[str, Any]:
    """Compact Mission Control row: Hard / Soft / Overall + density."""
    ev = evaluate_completion(entity)
    dens = ev.get("density") or {}
    return {
        "company": entity.upper(),
        "hard_pct": ev.get("hard_pct"),
        "soft_pct": ev.get("soft_pct"),
        "overall_pct": ev.get("overall_pct"),
        "years": ev.get("history_years"),
        "documents": dens.get("documents"),
        "extracts": dens.get("extracts"),
        "embeddings": dens.get("embeddings"),
        "density": dens.get("density"),
        "density_score": dens.get("density_score"),
        "mode": ev.get("mode"),
    }
