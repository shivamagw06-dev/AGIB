"""Ask orchestration observability — retrieval funnel, latency, entity confidence.

Internal telemetry for founder debugging. Not a user-facing surface.
"""

from __future__ import annotations

import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def new_ask_trace_id() -> str:
    """Stable per-request id: ASK-YYYYMMDD-<hex>."""
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"ASK-{day}-{secrets.token_hex(3).upper()}"


class StageTimer:
    """Accumulate wall-clock ms per named stage."""

    def __init__(self) -> None:
        self._t0 = time.perf_counter()
        self._marks: Dict[str, float] = {"start": self._t0}
        self.stages_ms: Dict[str, int] = {}

    def mark(self, name: str) -> None:
        now = time.perf_counter()
        prev = self._marks.get("_last", self._t0)
        self.stages_ms[name] = max(0, int((now - prev) * 1000))
        self._marks[name] = now
        self._marks["_last"] = now

    def total_ms(self) -> int:
        return max(0, int((time.perf_counter() - self._t0) * 1000))

    def as_dict(self) -> Dict[str, int]:
        out = dict(self.stages_ms)
        out["total"] = self.total_ms()
        return out

    def as_latency_block(self) -> Dict[str, int]:
        """Spec-shaped latency keys for diagnostics / Mission Control."""
        s = self.stages_ms
        return {
            "entity_ms": int(s.get("entity_resolution") or 0),
            "retrieval_ms": int(s.get("retrieval") or 0),
            "ranking_ms": int(s.get("ranking") or 0),
            "reasoning_ms": int(s.get("reasoning") or 0),
            "assembly_ms": int(
                s.get("response_assembly")
                or s.get("executive_assembly")
                or 0
            ),
            "serialization_ms": int(s.get("serialization") or 0),
            "http_ms": int(s.get("http") or 0),
            "total_ms": self.total_ms(),
            # Keep raw stage map for debugging
            "stages": dict(s),
        }


def _len_list(obj: Any) -> int:
    return len(obj) if isinstance(obj, list) else 0


def _pack_hit_count(pack: Any, *keys: str) -> int:
    if not isinstance(pack, dict):
        return 0
    n = 0
    for k in keys:
        v = pack.get(k)
        if isinstance(v, list):
            n += len(v)
        elif isinstance(v, dict):
            # nested hits / items / evidence_objects
            for nk in ("hits", "items", "evidence_objects", "documents", "articles"):
                if isinstance(v.get(nk), list):
                    n += len(v[nk])
    return n


def count_retrieved(
    *,
    kf_hits: Any = None,
    finance_retrieval: Any = None,
    live_evidence: Any = None,
    multi_source: Any = None,
    knowledge_corpus: Any = None,
    open_intelligence: Any = None,
    hits: Any = None,
    articles: Any = None,
    supporting: Any = None,
) -> int:
    n = 0
    n += _len_list(kf_hits)
    n += _pack_hit_count(finance_retrieval, "hits", "evidence")
    n += _pack_hit_count(live_evidence, "evidence_objects", "items", "hits")
    if isinstance(multi_source, dict):
        try:
            n += int(multi_source.get("evidence_count") or 0)
        except (TypeError, ValueError):
            n += _pack_hit_count(multi_source, "hits", "items", "evidence")
    n += _pack_hit_count(knowledge_corpus, "hits", "items")
    n += _pack_hit_count(open_intelligence, "hits", "items")
    n += _len_list(hits)
    n += _len_list(articles)
    n += _len_list(supporting)
    return n


def count_ranked(*, evidence_used: Any = None, supporting_research: Any = None, support_ev: Any = None) -> int:
    n = _len_list(evidence_used) + _len_list(supporting_research)
    if n == 0:
        n = _len_list(support_ev)
    return n


def count_passed_to_ice(ask_pipeline_runtime: Any, ice_view: Any) -> int:
    n = 0
    if isinstance(ask_pipeline_runtime, dict):
        ev = ask_pipeline_runtime.get("evidence") or {}
        if isinstance(ev, dict):
            n = max(n, _len_list(ev.get("items")))
        ia = ask_pipeline_runtime.get("institutional_answer") or {}
        if isinstance(ia, dict):
            ia_ev = ia.get("evidence") or {}
            if isinstance(ia_ev, dict):
                n = max(n, _len_list(ia_ev.get("items")))
    if isinstance(ice_view, dict):
        secs = ice_view.get("sections") or {}
        ev_sec = secs.get("evidence") if isinstance(secs, dict) else None
        if isinstance(ev_sec, dict):
            n = max(n, _len_list(ev_sec.get("bullets")))
        # sources / citations
        cites = ice_view.get("why") or []
        if isinstance(cites, list):
            n = max(n, min(len(cites), 14))
    return n


def count_referenced(
    *,
    ice_view: Any = None,
    evidence_used: Any = None,
    why: Any = None,
    executive: str = "",
) -> int:
    """Best-effort count of evidence actually reflected in the answer surface."""
    referenced_ids: set[str] = set()
    titles: List[str] = []

    if isinstance(ice_view, dict):
        secs = ice_view.get("sections") or {}
        for name in ("sources", "evidence", "analysis"):
            sec = secs.get(name) if isinstance(secs, dict) else None
            for b in (sec or {}).get("bullets") or []:
                s = str(b)
                if "evidence id" in s.lower() or "source=" in s.lower() or s.strip().startswith("-"):
                    referenced_ids.add(s[:120])
        for item in (ice_view.get("citations") or []) if isinstance(ice_view.get("citations"), list) else []:
            if isinstance(item, dict) and item.get("evidence_id"):
                referenced_ids.add(str(item["evidence_id"]))

    for item in evidence_used or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("source") or "").strip()
        if not title:
            continue
        titles.append(title)
        # Count as referenced if title fragment appears in executive/why
        blob = f"{executive} {' '.join(str(x) for x in (why or []))}".lower()
        needle = title.lower()[:40]
        if needle and needle in blob:
            referenced_ids.add(title)

    # If ICE why mentions "Supported by evidence" count those
    for line in why or []:
        low = str(line).lower()
        if "supported by evidence" in low or "evidence:" in low or "source:" in low:
            referenced_ids.add(str(line)[:120])

    if referenced_ids:
        return len(referenced_ids)
    # Soft floor: if we have evidence_used and a non-meta executive, credit min(1, n)
    if titles and executive and len(executive) >= 40:
        return min(len(titles), 3)
    return 0


def entity_confidence_block(
    *,
    detected_ticker: Optional[str],
    ere_body: Any,
    ticker_source: Optional[str],
    question: str,
    alias_hit: Optional[str] = None,
) -> Dict[str, Any]:
    ere = ere_body if isinstance(ere_body, dict) else {}
    aliases: List[str] = []
    if detected_ticker:
        aliases.append(detected_ticker)
    if alias_hit and alias_hit not in aliases:
        aliases.append(alias_hit)
    canon = ere.get("entity") or ere.get("canonical_entity")
    if isinstance(canon, dict):
        name = canon.get("canonical_name") or canon.get("name")
        if name:
            aliases.append(str(name))
        for a in canon.get("aliases") or []:
            if str(a) not in aliases:
                aliases.append(str(a))
    elif isinstance(canon, str) and canon not in aliases:
        aliases.append(canon)
    if ere.get("entity") and isinstance(ere.get("entity"), str):
        if ere["entity"] not in aliases:
            aliases.append(str(ere["entity"]))

    conf = ere.get("confidence")
    try:
        conf_f = float(conf) if conf is not None else None
    except (TypeError, ValueError):
        conf_f = None
    # Normalize 0-1 vs 0-100
    if conf_f is not None and conf_f > 1.0:
        conf_f = conf_f / 100.0

    if ticker_source in {"alias", "alias_override", "alias_final"} and detected_ticker:
        conf_f = max(conf_f or 0.0, 0.98)
    elif ticker_source == "ere" and detected_ticker:
        conf_f = conf_f if conf_f is not None else 0.9
    elif ticker_source == "user" and detected_ticker:
        conf_f = max(conf_f or 0.0, 0.95)
    elif detected_ticker:
        conf_f = conf_f if conf_f is not None else 0.55
    else:
        conf_f = conf_f if conf_f is not None else 0.0

    needs_clarification = bool(ere.get("needs_clarification") or ere.get("research_blocked"))
    low_confidence = bool(detected_ticker) and conf_f < 0.7

    name = None
    if isinstance(ere.get("entity"), str):
        name = ere.get("entity")
    elif isinstance(canon, dict):
        name = canon.get("canonical_name") or canon.get("name")
    if not name and detected_ticker:
        name = detected_ticker

    return {
        "name": name,
        "detected": detected_ticker,
        "entity_name": name,
        "entity_type": ere.get("entity_type"),
        "aliases_matched": aliases[:8],
        "confidence": round(conf_f, 3),
        "source": ticker_source,
        "resolution_source": ticker_source,
        "needs_clarification": needs_clarification or low_confidence,
        "low_confidence": low_confidence,
        "silently_bound": bool(low_confidence and ticker_source not in {"user", "alias", "alias_override", "alias_final", "ere"}),
        "question_excerpt": (question or "")[:160],
    }


def executive_attribution(
    *,
    executive: str,
    evidence_used: Any = None,
    supporting_research: Any = None,
    ice_view: Any = None,
) -> List[Dict[str, Any]]:
    """Map executive sentences/paragraphs to likely evidence titles (internal)."""
    text = (executive or "").strip()
    if not text:
        return []
    # Split on sentence-ish boundaries
    parts = [p.strip() for p in text.replace("·", ".").split(".") if len(p.strip()) >= 24]
    if not parts:
        parts = [text[:280]]

    corpus: List[Dict[str, str]] = []
    for item in list(evidence_used or []) + list(supporting_research or []):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        source = str(item.get("source") or item.get("provider") or item.get("type") or "").strip()
        if title or source:
            corpus.append({"title": title or source, "source": source or "evidence"})

    if isinstance(ice_view, dict):
        for b in ((ice_view.get("sections") or {}).get("sources") or {}).get("bullets") or []:
            corpus.append({"title": str(b)[:120], "source": "ice_sources"})

    rows: List[Dict[str, Any]] = []
    for i, para in enumerate(parts[:6], 1):
        low = para.lower()
        match = None
        for c in corpus:
            needle = (c["title"] or "").lower()[:32]
            if needle and any(tok in low for tok in needle.split()[:3] if len(tok) > 3):
                match = c
                break
        rows.append(
            {
                "paragraph": i,
                "text_excerpt": para[:180],
                "evidence_title": (match or {}).get("title"),
                "evidence_source": (match or {}).get("source"),
                "grounded": bool(match),
            }
        )
    return rows


def build_funnel(
    *,
    retrieved: int,
    ranked: int,
    passed: int,
    referenced: int,
) -> Dict[str, Any]:
    # Clamp monotonic-ish for display (referenced can exceed passed on soft credit)
    ranked = min(ranked, retrieved) if retrieved else ranked
    passed = min(passed, ranked) if ranked else passed
    utilization = (referenced / passed) if passed else 0.0
    efficiency = (referenced / retrieved) if retrieved else 0.0
    precision = (referenced / ranked) if ranked else 0.0
    return {
        "retrieved": retrieved,
        "ranked": ranked,
        "passed": passed,
        "passed_to_ice": passed,  # alias for older consumers
        "referenced": referenced,
        "utilization": round(min(utilization, 1.0), 3),
        "efficiency": round(min(efficiency, 1.0), 3),
        "precision": round(min(precision, 1.0), 3),
        "zero_stage": (
            "retrieved"
            if retrieved == 0
            else "ranked"
            if ranked == 0
            else "passed"
            if passed == 0
            else "referenced"
            if referenced == 0
            else None
        ),
    }


def format_trace_summary(orch: Dict[str, Any]) -> str:
    ent = orch.get("entity") or {}
    evidence = orch.get("evidence") or orch.get("funnel") or {}
    lat = orch.get("latency") or orch.get("latency_ms") or {}
    total = lat.get("total_ms") if lat.get("total_ms") is not None else lat.get("total") or 0
    return (
        f"Trace: {orch.get('ask_trace_id') or '—'} | "
        f"Entity: {ent.get('name') or ent.get('detected') or ent.get('entity_name') or '—'} "
        f"({ent.get('confidence', 0)}) | "
        f"Retrieved: {evidence.get('retrieved', 0)} → Ranked: {evidence.get('ranked', 0)} → "
        f"Passed: {evidence.get('passed', evidence.get('passed_to_ice', 0))} → "
        f"Referenced: {evidence.get('referenced', 0)} | "
        f"Utilization: {evidence.get('utilization', 0)} | "
        f"Efficiency: {evidence.get('efficiency', 0)} | "
        f"Precision: {evidence.get('precision', 0)} | "
        f"Executive overwritten: {'Yes' if orch.get('executive_overwritten') else 'No'} | "
        f"Fallback: {'Yes' if orch.get('fallback') or orch.get('fallback_used') else 'No'} | "
        f"Total: {float(total) / 1000:.1f}s"
    )


def finalize_orchestration(
    base: Dict[str, Any],
    *,
    timer: StageTimer,
    question: str,
    detected_ticker: Optional[str],
    ere_body: Any,
    alias_hit: Optional[str],
    kf_hits: Any = None,
    finance_retrieval: Any = None,
    live_evidence: Any = None,
    multi_source: Any = None,
    knowledge_corpus: Any = None,
    open_intelligence: Any = None,
    hits: Any = None,
    articles: Any = None,
    supporting: Any = None,
    evidence_used: Any = None,
    supporting_research: Any = None,
    support_ev: Any = None,
    ask_pipeline_runtime: Any = None,
    ice_view: Any = None,
    why: Any = None,
    executive: str = "",
    intent: Any = None,
    fallback: bool = False,
    persist: bool = True,
) -> Dict[str, Any]:
    orch = dict(base or {})
    ticker_source = orch.get("ticker_source")
    ask_trace_id = orch.get("ask_trace_id") or new_ask_trace_id()
    retrieved = count_retrieved(
        kf_hits=kf_hits,
        finance_retrieval=finance_retrieval,
        live_evidence=live_evidence,
        multi_source=multi_source,
        knowledge_corpus=knowledge_corpus,
        open_intelligence=open_intelligence,
        hits=hits,
        articles=articles,
        supporting=supporting,
    )
    ranked = count_ranked(
        evidence_used=evidence_used,
        supporting_research=supporting_research,
        support_ev=support_ev,
    )
    passed = count_passed_to_ice(ask_pipeline_runtime, ice_view)
    if passed == 0 and ranked:
        # Soft: ranked pack was available to reasoning even if ICE empty
        passed = min(ranked, 6)
    referenced = count_referenced(
        ice_view=ice_view,
        evidence_used=evidence_used,
        why=why,
        executive=executive,
    )
    funnel = build_funnel(
        retrieved=retrieved, ranked=ranked, passed=passed, referenced=referenced
    )
    entity = entity_confidence_block(
        detected_ticker=detected_ticker,
        ere_body=ere_body,
        ticker_source=ticker_source,
        question=question,
        alias_hit=alias_hit,
    )
    rejects = list(orch.get("ticker_rejects") or [])
    entity["rejected_candidates"] = [
        (r.get("raw") if isinstance(r, dict) else r) for r in rejects
    ][:12]
    attribution = executive_attribution(
        executive=executive,
        evidence_used=evidence_used,
        supporting_research=supporting_research,
        ice_view=ice_view,
    )
    grounded = (
        sum(1 for a in attribution if a.get("grounded")) / len(attribution) if attribution else None
    )
    ice_meta = bool(
        ((orch.get("ice_framework_meta_suppressed")) or False)
        or (
            isinstance(ice_view, dict)
            and (ice_view.get("institutional_communication") or {}).get("executive_was_framework_meta")
        )
    )
    # executive_overwritten: ICE tried to replace with meta and we suppressed, or ice won
    executive_overwritten = bool(orch.get("executive_source") == "ice") and not ice_meta

    latency = timer.as_latency_block()
    orch.update(
        {
            "version": "ask-orchestration-trace-2",
            "ask_trace_id": ask_trace_id,
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "fallback": fallback,
            "fallback_used": fallback,
            "engine_reached": not fallback,
            "intent": intent,
            "bound_ticker": detected_ticker,
            "entity": entity,
            "funnel": funnel,
            "evidence": {
                "retrieved": funnel["retrieved"],
                "ranked": funnel["ranked"],
                "passed": funnel["passed"],
                "referenced": funnel["referenced"],
                "utilization": funnel["utilization"],
                "efficiency": funnel["efficiency"],
                "precision": funnel["precision"],
                "zero_stage": funnel["zero_stage"],
            },
            "latency": latency,
            "latency_ms": timer.as_dict(),  # backward compatible
            "executive_attribution": attribution,
            "grounding": round(grounded, 3) if grounded is not None else None,
            "executive_overwritten": executive_overwritten,
            "executive_source": orch.get("executive_source"),
            "diagnostics_visibility": "internal",  # not end-user product copy
            "trace_summary": "",
        }
    )
    orch["trace_summary"] = format_trace_summary(orch)
    if persist:
        try:
            from app.ui.ask_observability_store import record_trace

            record_trace(orch)
        except Exception:
            pass
    return orch
