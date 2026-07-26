"""FAA v1 — Finance Acquisition Agent (upstream of FRE)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.faa.cache import DocumentCache
from app.faa.discovery import DiscoveryService
from app.faa.service import FaaService
from app.fre.service import FreService
from app.fre.store import FreStore
from app.main import app


def _stack():
    fre = FreService(store=FreStore())
    faa = FaaService(fre=fre)
    fre.bind(faa=faa)
    return fre, faa


def test_faa_health_locked():
    _, faa = _stack()
    h = faa.health()
    assert h["programme"] == "FAA"
    assert h["architecture_status"] == "v1.0.1 LOCKED"
    assert h["does_not_answer"] is True
    assert h["never_reasons"] is True
    assert h["fre_bound"] is True
    assert "discovery" in h["services"]


def test_discovery_reliance_tasks():
    disco = DiscoveryService(live_fetch=False)
    tasks, candidates = disco.discover("Should I buy Reliance?")
    assert len(tasks) >= 4
    assert any(t.connector_id == "company_ir" for t in tasks)
    assert any(t.connector_id == "nse" for t in tasks)
    assert any("ril.com" in (c.url or "") for c in candidates)


def test_acquire_indexes_into_fre_offline():
    fre, faa = _stack()
    before = fre.store.snapshot()["documents"]
    result = faa.acquire("Should I buy Reliance?", limit=16)
    assert result["does_not_answer"] is True
    assert result["live_fetch"] is False
    assert result["discovered"] >= 1
    assert result["indexed_to_fre"] >= 1
    after = fre.store.snapshot()["documents"]
    assert after >= before


def test_cache_skips_second_download():
    fre, faa = _stack()
    first = faa.acquire("Analyse Infosys", limit=12)
    second = faa.acquire("Analyse Infosys", limit=12)
    assert first["indexed_to_fre"] >= 1
    assert second["skipped_cached"] >= 1


def test_fre_query_calls_faa_acquisition_block():
    fre, _ = _stack()
    pack = fre.query("Should I buy Reliance?", limit=5)
    assert "acquisition" in pack
    assert pack["acquisition"]["programme"] == "FAA"
    assert pack["acquisition"]["discovered"] is not None
    assert pack["does_not_answer"] is True
    assert pack["top_evidence"]


def test_document_cache_checksum():
    cache = DocumentCache()
    cache.put(url="https://example.com/a", checksum="abc", title="A")
    skip, reason = cache.should_skip("https://example.com/a")
    assert skip is True
    assert reason == "url_cached"


@pytest.mark.asyncio
async def test_faa_http_health_and_acquire():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": "Bearer dev-intelligence-token"}
        health = await client.get("/v1/faa/health", headers=headers)
        assert health.status_code == 200
        body = health.json()
        assert body["programme"] == "FAA"
        assert body["architecture_status"] == "v1.0.1 LOCKED"

        acq = await client.post(
            "/v1/faa/acquire",
            params={"q": "Should I buy Reliance?", "limit": 12},
            headers=headers,
        )
        assert acq.status_code == 200
        data = acq.json()
        assert data["does_not_answer"] is True
        assert data["discovered"] >= 1
