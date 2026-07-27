"""KIP snapshot persistence — round-trip and integrity checks."""

from __future__ import annotations

from pathlib import Path

from app.kip.models import DocumentMetadata, InvestmentMetadata, KipChunk, KipDocument
from app.kip.persist import integrity_report, load_store, save_store, verify_document_retrievable
from app.kip.store import KipStore


def _seed(store: KipStore) -> str:
    doc = KipDocument(
        document_id="doc_persist_test01",
        lineage_id="lin_persist_test01",
        article_id="article-persist-1",
        content="ROIC and WACC persistence test for institutional memory.",
        cleaned_content="ROIC and WACC persistence test for institutional memory.",
        document=DocumentMetadata(title="Persist Test Note", document_type="agi_note"),
        investment=InvestmentMetadata(tickers=["TESTCO"], themes=["valuation"]),
    )
    chunks = [
        KipChunk(
            chunk_id="chk_persist_1",
            document_id=doc.document_id,
            lineage_id=doc.lineage_id,
            text=doc.cleaned_content,
            embedding=[0.1] * 8,
            tickers=["TESTCO"],
            themes=["valuation"],
        )
    ]
    store.put_document(doc, chunks)
    return doc.document_id


def test_kip_snapshot_roundtrip(tmp_path: Path):
    path = tmp_path / "kip_snapshot.json"
    store = KipStore()
    doc_id = _seed(store)
    saved = save_store(store, path=path)
    assert saved["ok"] is True
    assert saved["documents"] == 1
    assert path.exists()

    restored = KipStore()
    loaded = load_store(restored, path=path)
    assert loaded["ok"] is True
    assert loaded["loaded"] is True
    assert restored.get_document(doc_id) is not None
    assert len(restored.chunks) == 1
    assert verify_document_retrievable(restored, doc_id)["retrievable"] is True

    report = integrity_report(restored)
    assert report["healthy"] is True
    assert report["stats"]["vector_chunks"] == 1


def test_integrity_detects_missing_doc(tmp_path: Path):
    store = KipStore()
    _seed(store)
    report = integrity_report(store, expected_document_ids=["doc_missing_xyz"])
    assert report["healthy"] is False
    assert "doc_missing_xyz" in report["expected_missing_ids"]
