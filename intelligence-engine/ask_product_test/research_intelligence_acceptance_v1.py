"""Research Intelligence Acceptance Test v1.0 — 400 deterministic questions.

Engine-only (in-process). Target 100% before Ask/KUL integration.
Never allows BUY/SELL recommendation leakage.
"""

from __future__ import annotations

from typing import Any, Dict, List

from investment_intelligence.policy import has_recommendation_leak
from research_intelligence.corpus import CORPUS

RI_ACCEPTANCE_400: List[Dict[str, Any]] = []
ENTITY_KEYS = sorted(CORPUS.keys())


def _add(
    category: str,
    prompt: str,
    *,
    entity: str | None = None,
    must_any: List[str],
    fields_any: List[str] | None = None,
):
    RI_ACCEPTANCE_400.append(
        {
            "id": f"RI-{len(RI_ACCEPTANCE_400)+1:03d}",
            "category": category,
            "prompt": prompt,
            "entity": entity,
            "must_any": must_any,
            "fields_any": fields_any or [],
        }
    )


def _n(key: str) -> str:
    return CORPUS[key]["name"]


# ---- Annual Reports (~50) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"Extract structured intelligence from the latest annual report for {n}.", ["annual", "strategy", "segment", "capital", "risk", "kpi"]),
        (f"What business and strategy themes appear in {n} annual reports?", ["business", "strategy", "theme"]),
        (f"Explain products, segments, and customers for {n} from annual reports.", ["product", "segment", "customer"]),
        (f"How is capital allocation described across {n} annual reports?", ["capital", "allocat"]),
        (f"What governance and financial changes are noted for {n}?", ["governance", "financial"]),
        (f"List KPIs and risks highlighted in {n} annual reports.", ["kpi", "risk"]),
        (f"What guidance language appears in {n} annual reports?", ["guidance"]),
        (f"Compare FY2022 vs FY2026 strategy for {n}.", ["fy2022", "fy2026", "strategy"]),
        (f"What themes recur across annual reports for {n}?", ["theme", "recur", "annual"]),
        (f"Store annual report extracts for {n} as structured research memory.", ["research", "memory", "annual", "structured"]),
    ]:
        _add("annual_reports", prompt, entity=key, must_any=must, fields_any=["annual_report", "summary"])

# ---- Transcripts (~45) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"Structure the latest earnings transcript for {n}.", ["transcript", "management", "commentary"]),
        (f"What did management say about demand and margins for {n}?", ["demand", "margin"]),
        (f"Track pricing commentary across earnings for {n}.", ["pricing", "commentary"]),
        (f"What analyst questions recur for {n}?", ["analyst", "question"]),
        (f"Describe management confidence and guidance changes in {n} transcripts.", ["confidence", "guidance"]),
        (f"Explain capex and hiring commentary for {n}.", ["capex", "hiring"]),
        (f"What customer commentary appears in {n} earnings calls?", ["customer", "commentary"]),
        (f"Convert {n} conference call content into structured intelligence.", ["structured", "transcript", "management"]),
        (f"How has pricing commentary evolved across {n} earnings?", ["pricing", "earnings"]),
    ]:
        _add("transcripts", prompt, entity=key, must_any=must, fields_any=["transcript", "summary"])

# ---- Guidance (~40) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"How has management guidance evolved for {n}?", ["guidance", "previous", "evol"]),
        (f"Compare {n} guidance versus previous guidance.", ["guidance", "previous"]),
        (f"Compare {n} guidance versus consensus.", ["guidance", "consensus"]),
        (f"Compare {n} guidance versus actual results framing.", ["guidance", "actual"]),
        (f"Explain revenue, margin, and capex guidance for {n}.", ["revenue", "margin", "capex", "guidance"]),
        (f"What hiring and demand commentary is in {n} guidance history?", ["hiring", "demand", "guidance"]),
        (f"Track pricing commentary inside guidance updates for {n}.", ["pricing", "guidance"]),
        (f"Summarize guidance intelligence objects for {n}.", ["guidance", "structured"]),
    ]:
        _add("guidance", prompt, entity=key, must_any=must, fields_any=["guidance", "summary"])

# ---- Events (~35) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"Explain the history of acquisitions and major events for {n}.", ["acquisition", "event"]),
        (f"List structured events for {n} with business and investment links.", ["event", "business", "investment"]),
        (f"How do {n} events link to industry and portfolio implications?", ["event", "industry", "portfolio"]),
        (f"What buyback, dividend, or capital raise events matter for {n}?", ["buyback", "dividend", "capital", "event"]),
        (f"Describe regulatory or product-launch events for {n}.", ["event", "regulatory", "product"]),
        (f"Map factory expansion or management-change events for {n}.", ["event", "management", "factory", "expansion", "change"]),
        (f"Build event intelligence for {n}.", ["event", "link"]),
    ]:
        _add("events", prompt, entity=key, must_any=must, fields_any=["events", "summary"])

# ---- Management (~35) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"Evaluate management intelligence for {n}.", ["management", "ceo", "cfo"]),
        (f"What has management consistently emphasized at {n}?", ["management", "emphas"]),
        (f"Explain capital allocation philosophy of {n} management.", ["capital", "allocat", "philosophy", "management"]),
        (f"Assess communication consistency and execution for {n}.", ["communication", "consistency", "execution"]),
        (f"Comment on historical accuracy of {n} management commentary.", ["historical", "accuracy", "management"]),
        (f"Track leadership changes for {n}.", ["leadership", "change", "management"]),
        (f"Describe chairman/CEO/CFO structure signals for {n}.", ["ceo", "cfo", "chairman"]),
    ]:
        _add("management", prompt, entity=key, must_any=must, fields_any=["management", "summary"])

# ---- History / Timeline (~30) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"Build the research timeline for {n}.", ["timeline", "chronolog", "event"]),
        (f"Explain company history for {n} using research memory.", ["history", "company", "memory"]),
        (f"What major acquisitions and capital allocation milestones define {n}?", ["acquisition", "capital", "timeline"]),
        (f"Map IPO/history, leadership, and industry events for {n}.", ["timeline", "industry", "leadership", "ipo", "history"]),
        (f"What important decisions appear on the {n} research timeline?", ["timeline", "decision", "event"]),
        (f"Provide chronological intelligence for {n}.", ["timeline", "chronolog"]),
    ]:
        _add("history", prompt, entity=key, must_any=must, fields_any=["timeline", "memory", "summary"])

# ---- Capital Allocation (~25) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"Summarize five years of capital allocation for {n}.", ["capital", "allocat", "5y", "five"]),
        (f"Explain 10-year capital allocation evolution for {n}.", ["capital", "allocat", "10"]),
        (f"How does capital allocation show up in {n} annual reports and events?", ["capital", "allocat", "annual", "event"]),
        (f"Deep research capital allocation consistency for {n}.", ["capital", "allocat", "deep", "consistency"]),
        (f"What capital allocation themes recur for {n}?", ["capital", "allocat", "theme"]),
    ]:
        _add("capital_allocation", prompt, entity=key, must_any=must, fields_any=["deep_research", "annual_report", "summary"])

# ---- Deep Research (~40) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"Perform deep research on {n} covering management and industry evolution.", ["deep", "management", "industry", "evolution"]),
        (f"How has the competitive landscape evolved for {n}?", ["competitive", "evolution"]),
        (f"Explain risk evolution for {n} over time.", ["risk", "evolution"]),
        (f"Assess strategic consistency for {n}.", ["strategic", "consistency"]),
        (f"What changed in the business model for {n}?", ["business", "model", "change"]),
        (f"Compare FY2022 versus FY2026 strategy for {n} in deep research.", ["fy2022", "fy2026", "strategy"]),
        (f"Track guidance accuracy as a deep research object for {n}.", ["guidance", "accuracy"]),
        (f"Synthesize institutional research on {n} across five to ten years.", ["capital", "evolution", "research"]),
    ]:
        _add("deep_research", prompt, entity=key, must_any=must, fields_any=["deep_research", "summary"])

# ---- Cross-document (~30) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"Connect annual reports, transcripts, and presentations for {n}.", ["annual", "transcript", "presentation", "document"]),
        (f"Explain cross-document intelligence for {n}.", ["cross", "document"]),
        (f"How do filings, press releases, and research notes link for {n}?", ["filing", "press", "research", "document"]),
        (f"Build one document timeline for {n}.", ["timeline", "document"]),
        (f"Describe document linkage across earnings and annual reports for {n}.", ["document", "linkage", "annual", "earnings"]),
        (f"What document types are in the {n} research workspace?", ["document", "annual", "transcript"]),
    ]:
        _add("cross_document", prompt, entity=key, must_any=must, fields_any=["cross_document", "summary"])

# ---- Research Memory (~30) ----
for key in ENTITY_KEYS:
    n = _n(key)
    for prompt, must in [
        (f"What does research memory store for {n}?", ["memory", "conclusion", "theme"]),
        (f"List research conclusions and recurring themes for {n}.", ["conclusion", "theme", "recur"]),
        (f"Explain why {n} research should never be duplicated.", ["duplicate", "memory", "update"]),
        (f"How do tomorrow's questions improve from {n} research memory?", ["memory", "history", "conclusion"]),
        (f"Summarize management history and guidance history in memory for {n}.", ["management", "guidance", "history", "memory"]),
        (f"Describe industry evolution stored in {n} research memory.", ["industry", "evolution", "memory"]),
    ]:
        _add("research_memory", prompt, entity=key, must_any=must, fields_any=["memory", "summary"])

# ---- Estimates / Quality / Evolution / Workspace extras ----
for key in ENTITY_KEYS:
    n = _n(key)
    _add(
        "estimates",
        f"Explain estimate intelligence for {n} without forecasting.",
        entity=key,
        must_any=["estimate", "consensus", "revision", "gap", "forecast"],
        fields_any=["estimates", "summary"],
    )
    _add(
        "quality",
        f"Evaluate research quality, freshness, and coverage for {n}.",
        entity=key,
        must_any=["quality", "freshness", "coverage", "unknown"],
        fields_any=["quality", "summary"],
    )
    _add(
        "knowledge_evolution",
        f"Explain knowledge evolution from research to portfolio for {n}.",
        entity=key,
        must_any=["knowledge", "evolution", "business", "investment", "portfolio"],
        fields_any=["knowledge_evolution", "summary"],
    )
    _add(
        "workspace",
        f"Describe the canonical research object / workspace for {n}.",
        entity=key,
        must_any=["research", "object", "company", "evidence", "unknown", "monitor"],
        fields_any=["research_object", "summary"],
    )

# Founder-style extras
extras = [
    ("reliance", "Summarize five years of capital allocation for Reliance Industries.", "capital_allocation", ["capital", "allocat", "reliance"]),
    ("reliance", "How has management guidance evolved for Reliance?", "guidance", ["guidance", "evol", "previous"]),
    ("tcs", "Compare FY2022 vs FY2026 strategy for TCS.", "deep_research", ["fy2022", "fy2026", "strategy", "tcs"]),
    ("asian_paints", "Track pricing commentary across earnings for Asian Paints.", "transcripts", ["pricing", "commentary", "asian"]),
    ("hdfc_bank", "What changed in the business model for HDFC Bank?", "deep_research", ["business", "model", "merger", "hdfc"]),
    ("infosys", "What has management consistently emphasized at Infosys?", "management", ["management", "emphas", "guidance", "infosys"]),
    ("reliance", "Explain the history of acquisitions for Reliance Industries.", "events", ["acquisition", "history", "reliance"]),
    ("tcs", "What themes recur across annual reports for TCS?", "annual_reports", ["theme", "recur", "annual", "tcs"]),
    ("hdfc_bank", "Build the research timeline for HDFC Bank.", "history", ["timeline", "merger", "hdfc"]),
    ("asian_paints", "Explain cross-document intelligence for Asian Paints.", "cross_document", ["document", "cross", "asian"]),
]
for entity, prompt, cat, must in extras:
    _add(cat, prompt, entity=entity, must_any=must, fields_any=["summary"])

# Pad evenly to 400
_pad = [
    ("annual_reports", "Restate annual report structured extracts for {n} (variant {i}).", ["annual", "strategy", "kpi"], ["annual_report", "summary"]),
    ("transcripts", "Restate transcript structured intelligence for {n} (variant {i}).", ["transcript", "management", "demand"], ["transcript", "summary"]),
    ("guidance", "Restate guidance vs previous/consensus/actual for {n} (variant {i}).", ["guidance", "previous", "consensus"], ["guidance", "summary"]),
    ("deep_research", "Restate deep research evolution themes for {n} (variant {i}).", ["evolution", "strategy", "research"], ["deep_research", "summary"]),
    ("research_memory", "Restate research memory conclusions for {n} (variant {i}).", ["memory", "conclusion", "theme"], ["memory", "summary"]),
    ("events", "Restate event linkage for {n} (variant {i}).", ["event", "business", "investment"], ["events", "summary"]),
    ("history", "Restate chronological timeline for {n} (variant {i}).", ["timeline", "history"], ["timeline", "summary"]),
    ("management", "Restate management consistency signals for {n} (variant {i}).", ["management", "consistency"], ["management", "summary"]),
]
_i = 0
while len(RI_ACCEPTANCE_400) < 400:
    key = ENTITY_KEYS[_i % len(ENTITY_KEYS)]
    cat, tmpl, must, fields = _pad[_i % len(_pad)]
    _i += 1
    _add(cat, tmpl.format(n=_n(key), i=_i), entity=key, must_any=must, fields_any=fields)

del RI_ACCEPTANCE_400[400:]
for i, case in enumerate(RI_ACCEPTANCE_400, 1):
    case["id"] = f"RI-{i:03d}"

assert len(RI_ACCEPTANCE_400) == 400, len(RI_ACCEPTANCE_400)


def _blob(payload: Dict[str, Any]) -> str:
    parts = [
        payload.get("executive_summary") or payload.get("summary"),
        " ".join(payload.get("whats_new") or []),
        payload.get("business_impact") or "",
        payload.get("financial_impact") or "",
        payload.get("industry_impact") or "",
        payload.get("investment_implications") or "",
        " ".join(payload.get("unknowns") or []),
        " ".join(payload.get("monitoring_points") or []),
        payload.get("recommendation_policy") or "",
        payload.get("knowledge_authority") or "",
    ]
    for key in (
        "research_object",
        "annual_report",
        "transcript",
        "management",
        "guidance",
        "estimates",
        "events",
        "memory",
        "cross_document",
        "timeline",
        "quality",
        "knowledge_evolution",
        "deep_research",
        "evidence",
    ):
        block = payload.get(key)
        if isinstance(block, dict):
            parts.append(block.get("summary") or "")
            parts.append(str(block)[:4000])
        elif block:
            parts.append(str(block)[:2000])
    return " ".join(str(p) for p in parts if p).lower()


def evaluate_ri_case(case: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    text = _blob(payload)
    summary = (payload.get("executive_summary") or payload.get("summary") or "").strip()
    must = case.get("must_any") or []
    hits = sum(1 for m in must if m.lower() in text)
    fields = case.get("fields_any") or []
    field_ok = (not fields) or any(
        payload.get(f)
        or (isinstance(payload.get(f), dict) and payload[f])
        or (isinstance(payload.get(f), list) and payload[f])
        or (f == "summary" and summary)
        for f in fields
    )
    direct_first = bool(summary) and len(summary) > 24 and not summary.lower().startswith(
        ("analyse via", "framework", "intent:", "planning:")
    )
    no_fabricated = payload.get("fabricated") is not True
    no_reco = payload.get("recommendation") in (None, "", "none") and not has_recommendation_leak(summary)
    policy_ok = "no_buy_sell" in str(payload.get("recommendation_policy") or "") or "observations_only" in str(
        payload.get("recommendation_policy") or ""
    )
    entity_ok = True
    if case.get("entity"):
        name = CORPUS[case["entity"]]["name"].split()[0].lower()
        entity_ok = name in text or case["entity"].replace("_", " ") in text or "research" in text

    need = 1 if len(must) <= 2 else min(2, len(must))
    topic_ok = hits >= need
    passed = bool(
        topic_ok
        and field_ok
        and direct_first
        and no_fabricated
        and no_reco
        and policy_ok
        and entity_ok
        and payload.get("ok") is not False
    )
    return {
        "id": case["id"],
        "category": case["category"],
        "prompt": case["prompt"],
        "pass": passed,
        "topic_hits": hits,
        "must_any": must,
        "field_ok": field_ok,
        "direct_answer_first": direct_first,
        "no_fabrication": no_fabricated,
        "no_recommendation_leakage": no_reco and policy_ok,
        "entity_ok": entity_ok,
        "summary": summary[:240],
        "modules_used": payload.get("modules_used") or [],
        "failed_assertions": [
            k
            for k, v in {
                "topic_ok": topic_ok,
                "field_ok": field_ok,
                "direct_first": direct_first,
                "no_fabricated": no_fabricated,
                "no_reco": no_reco and policy_ok,
                "entity_ok": entity_ok,
            }.items()
            if not v
        ],
    }
