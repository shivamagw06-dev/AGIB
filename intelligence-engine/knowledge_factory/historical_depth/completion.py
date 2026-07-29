"""Multi-dimension completion criteria for institutional historical backfill."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from knowledge_factory.historical_depth import store as hd_store

TARGET_YEARS = float(os.getenv("KF_HD_TARGET_YEARS") or "15")

# Hard gates — company cannot leave backlog until these pass (or N/A with attempt).
HARD_DIMS = (
    "ohlcv",
    "corporate_actions",
    "financials_annual",
    "financials_quarterly",
    "knowledge_extract",
    "embeddings",
    "qa",
)

# Soft gates — attempt recorded OR present; transparent unavailability does not block forever.
SOFT_DIMS = (
    "announcements",
    "annual_reports",
    "investor_presentations",
    "earnings_transcripts",
    "shareholding",
    "macro_linked",
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
        span = max(0.5, (datetime.now(timezone.utc).replace(tzinfo=None) - listed.replace(tzinfo=None)).days / 365.25)
        # If Yahoo returned full history and span < target, company is "as complete as listing allows"
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


def evaluate_completion(entity: str, *, target_years: float | None = None) -> dict[str, Any]:
    """Return per-dimension status and whether company is Fully Backfilled."""
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

    # QA on prices
    qa_ok = True
    try:
        from live_data.qa import qa_price_points

        qa = qa_price_points(list(prices.get("records") or []))
        qa_ok = bool(qa.get("ok")) if prices.get("records") else False
    except Exception:
        qa_ok = bool(prices.get("records"))

    ohlcv_ok = years + 1e-9 >= eff and len(prices.get("records") or []) >= 12
    # Corporate actions: present OR attempted empty (valid for some names)
    ca_n = len(actions.get("records") or [])
    ca_attempt = attempts.get("corporate_actions") or {}
    ca_ok = ca_n > 0 or ca_attempt.get("status") in {"complete", "empty", "n_a"}

    ann_n = len(annual.get("records") or [])
    # Annual: prefer real financials; price-proxy annual counts toward depth
    annual_ok = ann_n >= max(3, int(min(eff, target))) or (ohlcv_ok and ann_n >= int(eff * 0.5))

    q_n = len(quarterly.get("records") or [])
    q_need = max(4, int(min(eff, target) * 4 * 0.5))  # 50% of expected quarters
    quarterly_ok = q_n >= min(q_need, 8) or (eff < 2 and q_n >= 2)

    ar_ok = "annual_report" in doc_types or (attempts.get("annual_reports") or {}).get("status") in {
        "complete",
        "n_a",
        "empty",
    }
    ip_ok = "investor_presentation" in doc_types or (attempts.get("investor_presentations") or {}).get(
        "status"
    ) in {"complete", "n_a", "empty"}
    tr_ok = "earnings_transcript" in doc_types or (attempts.get("earnings_transcripts") or {}).get(
        "status"
    ) in {"complete", "n_a", "empty"}
    sh_ok = (attempts.get("shareholding") or {}).get("status") in {"complete", "n_a", "empty"} or bool(
        hd_store.get_series("shareholding", e)
    )
    ann_ex_ok = (attempts.get("announcements") or {}).get("status") in {"complete", "n_a", "empty"}
    try:
        from live_data import store as lidi_store

        snap = lidi_store.get_latest_snapshot("nse_announcements", "LATEST") or {}
        events = (snap.get("payload") or {}).get("events") or []
        if any(str(ev.get("symbol") or "").upper() == e for ev in events if isinstance(ev, dict)):
            ann_ex_ok = True
    except Exception:
        pass

    macro_ok = False
    try:
        macro_ok = len(hd_store.get_macro_history() or []) > 0
    except Exception:
        macro_ok = False

    dims = {
        "ohlcv": _dim(ohlcv_ok, detail=f"years={years:.2f} target={eff:.2f}"),
        "corporate_actions": _dim(ca_ok, n_a=ca_attempt.get("status") == "n_a", detail=f"n={ca_n}"),
        "announcements": _dim(ann_ex_ok, n_a=True if not ann_ex_ok else False, detail="exchange"),
        "financials_annual": _dim(annual_ok, detail=f"n={ann_n}"),
        "financials_quarterly": _dim(quarterly_ok, detail=f"n={q_n}"),
        "annual_reports": _dim(ar_ok, n_a=(attempts.get("annual_reports") or {}).get("status") == "n_a"),
        "investor_presentations": _dim(
            ip_ok, n_a=(attempts.get("investor_presentations") or {}).get("status") == "n_a"
        ),
        "earnings_transcripts": _dim(
            tr_ok, n_a=(attempts.get("earnings_transcripts") or {}).get("status") == "n_a"
        ),
        "shareholding": _dim(sh_ok, n_a=True),
        "macro_linked": _dim(macro_ok, detail="global_macro"),
        "knowledge_extract": _dim(_has_extract(e)),
        "embeddings": _dim(_has_embedding(e)),
        "qa": _dim(qa_ok, detail="price_qa"),
    }

    # Soft dims: missing without attempt → still blocks; n_a or complete → ok
    def _passes(name: str, soft: bool) -> bool:
        st = dims[name]["status"]
        if st == "complete":
            return True
        if soft and st == "n_a":
            return True
        return False

    hard_ok = all(_passes(d, soft=False) for d in HARD_DIMS)
    # Soft: treat missing as auto n_a after first full attempt wave (recorded)
    soft_ok = True
    for d in SOFT_DIMS:
        st = dims[d]["status"]
        if st == "complete":
            continue
        if st == "n_a":
            continue
        # Allow soft missing if we've recorded an attempt for this entity overall
        if attempts.get(d) or attempts.get("_wave"):
            dims[d] = _dim(False, n_a=True, detail="attempted_unavailable")
            continue
        soft_ok = False

    complete = hard_ok and soft_ok
    coverage = round(
        100.0
        * sum(1 for d in (*HARD_DIMS, *SOFT_DIMS) if dims[d]["status"] in {"complete", "n_a"})
        / max(1, len(HARD_DIMS) + len(SOFT_DIMS)),
        2,
    )
    return {
        "entity": e,
        "complete": complete,
        "fully_backfilled": complete,
        "history_years": round(years, 2),
        "effective_target_years": round(eff, 2),
        "configured_target_years": target,
        "coverage_pct": coverage,
        "dimensions": dims,
        "hard_ok": hard_ok,
        "soft_ok": soft_ok,
        "mode": "maintenance" if complete else "backfill",
    }
