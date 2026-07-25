"""RAG evidence packs — retrieval-augmented answers only; never model memory alone."""

from __future__ import annotations

from app.kip.models import KipDocument, RagEvidenceItem, RagEvidencePack, SearchHit
from app.kip.search import search


def build_evidence_pack(
    query: str,
    *,
    documents: dict[str, KipDocument],
    chunks: list,
    ticker: str | None = None,
    limit: int = 8,
    dim: int = 256,
) -> RagEvidencePack:
    result = search(
        query,
        documents=documents,
        chunks=chunks,
        mode="hybrid",
        limit=limit,
        ticker=ticker,
        dim=dim,
    )
    supporting: list[RagEvidenceItem] = []
    conflicting: list[RagEvidenceItem] = []
    sources: list[str] = []
    freshness_vals: list[float] = []
    conf_vals: list[float] = []

    for hit in result.hits:
        doc = documents.get(hit.document_id)
        if doc is None:
            continue
        item = _to_item(doc, hit)
        sources.append(f"{doc.document.source}:{doc.document.title}")
        freshness_vals.append(doc.knowledge.freshness)
        conf_vals.append(doc.knowledge.confidence)
        if item.stance == "bear" or _conflicts_with_query(query, doc):
            conflicting.append(item)
        else:
            supporting.append(item)

    # Explicit conflict detection: bull vs bear across retrieved set
    bulls = [i for i in supporting + conflicting if i.stance == "bull"]
    bears = [i for i in supporting + conflicting if i.stance == "bear"]
    if bulls and bears:
        for b in bears:
            if b not in conflicting:
                conflicting.append(b)

    freshness = sum(freshness_vals) / len(freshness_vals) if freshness_vals else 0.0
    confidence = sum(conf_vals) / len(conf_vals) if conf_vals else 0.0
    # Cap confidence when conflicts present
    if conflicting and bulls and bears:
        confidence *= 0.75

    return RagEvidencePack(
        query=query,
        documents_retrieved=[h.document_id for h in result.hits],
        supporting_evidence=supporting,
        conflicting_opinions=conflicting,
        source_list=sources,
        freshness_score=round(freshness, 4),
        confidence_score=round(confidence, 4),
        knowledge_version="kip-v1.0.1",
        answer_policy="retrieval_augmented_only",
    )


def research_writer_context(
    *,
    ticker: str | None,
    query: str,
    documents: dict[str, KipDocument],
    chunks: list,
    dim: int = 256,
) -> dict:
    """Retrieve institutional context for AGI research writing (no engine redesign)."""
    pack = build_evidence_pack(query, documents=documents, chunks=chunks, ticker=ticker, dim=dim)
    prior = []
    brokers = []
    filings = []
    transcripts = []
    macro = []
    for doc_id in pack.documents_retrieved:
        d = documents.get(doc_id)
        if d is None:
            continue
        dtype = d.document.document_type.value
        entry = {
            "document_id": d.document_id,
            "title": d.document.title,
            "type": dtype,
            "thesis": d.research.investment_thesis,
            "version": d.document.version,
            "date": d.document.date.isoformat() if d.document.date else None,
        }
        if dtype.startswith("agi_"):
            prior.append(entry)
        elif "broker" in dtype:
            brokers.append(entry)
        elif "filing" in dtype or "report" in dtype:
            filings.append(entry)
        elif "transcript" in dtype:
            transcripts.append(entry)
        elif "macro" in dtype or "central_bank" in dtype:
            macro.append(entry)
    return {
        "documents_retrieved": pack.documents_retrieved,
        "knowledge_version": pack.knowledge_version,
        "source_list": pack.source_list,
        "conflicting_evidence": [c.model_dump(mode="json") for c in pack.conflicting_opinions],
        "freshness_score": pack.freshness_score,
        "confidence_score": pack.confidence_score,
        "previous_agi_research": prior,
        "broker_reports": brokers,
        "filings": filings,
        "transcripts": transcripts,
        "macro_reports": macro,
        "supporting_evidence": [s.model_dump(mode="json") for s in pack.supporting_evidence],
    }


def _to_item(doc: KipDocument, hit: SearchHit) -> RagEvidenceItem:
    stance = "neutral"
    if doc.research.bull_case and not doc.research.bear_case:
        stance = "bull"
    elif doc.research.bear_case and not doc.research.bull_case:
        stance = "bear"
    elif doc.research.bull_case and doc.research.bear_case:
        # lean by counts
        stance = "bull" if len(doc.research.bull_case) >= len(doc.research.bear_case) else "bear"
    text_l = (doc.cleaned_content or "").lower()
    if any(w in text_l for w in ("downgrade", "sell", "underweight", "bearish")):
        stance = "bear"
    if any(w in text_l for w in ("upgrade", "buy", "overweight", "bullish")) and stance != "bear":
        stance = "bull"
    return RagEvidenceItem(
        document_id=doc.document_id,
        title=doc.document.title,
        snippet=hit.snippet or (doc.knowledge.summary or doc.research.investment_thesis)[:280],
        tickers=list(doc.investment.tickers),
        stance=stance,
        freshness=doc.knowledge.freshness,
        confidence=doc.knowledge.confidence,
        date=doc.document.date,
    )


def _conflicts_with_query(query: str, doc: KipDocument) -> bool:
    q = query.lower()
    if "bull" in q and doc.research.bear_case and not doc.research.bull_case:
        return True
    if "bear" in q and doc.research.bull_case and not doc.research.bear_case:
        return True
    return False
