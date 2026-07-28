"""Company Investor Relations collector — results/presentations/guidance links."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from live_data import store
from live_data.collectors.base import collector_envelope, fallback_to_snapshot, http_get, run_with_retry
from live_data.schema import DEFAULT_RETRY

COLLECTOR_ID = "lidi_company_ir_v1"
SOURCE_ID = "company_ir"
OFFICIAL = "Company IR websites"
SAMPLES = Path(__file__).resolve().parents[1] / "samples"

# Seed IR entrypoints for Track-1 names (live HEAD/GET probe; structured parse may be limited).
IR_ENTRYPOINTS: dict[str, str] = {
    "INFY": "https://www.infosys.com/investors.html",
    "TCS": "https://www.tcs.com/investor-relations",
    "RELIANCE": "https://www.ril.com/InvestorRelations.aspx",
    "HDFCBANK": "https://www.hdfcbank.com/personal/about-us/investor-relations",
    "WIPRO": "https://www.wipro.com/investors/",
}


def collect_company_ir(
    *,
    ticker: str = "INFY",
    injected_json: dict[str, Any] | str | None = None,
    allow_recorded_sample: bool = False,
) -> dict[str, Any]:
    t = str(ticker or "INFY").upper()
    mode = "live"
    payload_obj = None
    raw = None
    url_used = IR_ENTRYPOINTS.get(t)
    try:
        if injected_json is not None:
            mode = "injected"
            if isinstance(injected_json, str):
                payload_obj = json.loads(injected_json)
                raw = injected_json.encode("utf-8")
            else:
                payload_obj = injected_json
                raw = json.dumps(injected_json).encode("utf-8")
        else:
            def _fetch() -> bytes:
                if not url_used:
                    raise RuntimeError(f"no_ir_entrypoint:{t}")
                return http_get(
                    url_used,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AGIB-LIDI/1.0)", "Accept": "text/html,*/*"},
                    timeout=25,
                )

            try:
                policy = {"max_attempts": 1, "backoff_seconds": [0]} if allow_recorded_sample else DEFAULT_RETRY
                html = run_with_retry(_fetch, retry_policy=policy)
                # HTML pages are not structured filings — publish probe metadata + UNKNOWN docs unless sample/inject
                if b"pdf" not in html.lower() and b"result" not in html.lower():
                    raise RuntimeError("company_ir_page_without_detectable_filings")
                # Minimal structured extraction: presence flags only (no invented filings)
                payload_obj = {
                    "effective_date": store.utc_now()[:10],
                    "ticker": t,
                    "documents": [],
                    "ir_page_reachable": True,
                    "structured_filings": "UNKNOWN",
                    "note": "Live IR HTML reached; structured filing list requires site-specific adapters",
                }
                raw = json.dumps(payload_obj).encode("utf-8")
                mode = "live_probe"
            except Exception as live_exc:
                if allow_recorded_sample and t == "INFY":
                    sample = SAMPLES / "company_ir_infosys.json"
                    mode = "recorded_sample"
                    raw = sample.read_bytes()
                    payload_obj = json.loads(raw.decode("utf-8"))
                    url_used = str(sample)
                else:
                    fb = fallback_to_snapshot(
                        collector_id=COLLECTOR_ID,
                        source_id=SOURCE_ID,
                        entity=t,
                        reason=str(live_exc)[:200],
                    )
                    store.update_collector_health(
                        COLLECTOR_ID,
                        source=SOURCE_ID,
                        last_failure=store.utc_now(),
                        failure_count=(store.get_collector_health(COLLECTOR_ID).get("failure_count") or 0) + 1,
                        last_error=str(live_exc)[:200],
                        version=COLLECTOR_ID,
                        frequency="event_driven",
                        retry_policy=DEFAULT_RETRY,
                    )
                    return fb or {
                        "ok": False,
                        "collector_id": COLLECTOR_ID,
                        "source_id": SOURCE_ID,
                        "official_source": OFFICIAL,
                        "entity": t,
                        "reason": "live_unavailable_no_snapshot",
                        "error": str(live_exc)[:240],
                        "fixture": False,
                        "fabricated": False,
                        "transparent_insufficiency": True,
                    }

        assert payload_obj is not None and raw is not None
        docs = list(payload_obj.get("documents") or [])
        effective = payload_obj.get("effective_date")
        file_rec = store.put_raw_file(SOURCE_ID, f"{t}_ir.json", raw, meta={"mode": mode, "url": url_used})
        env = collector_envelope(
            collector_id=COLLECTOR_ID,
            source_id=SOURCE_ID,
            official_source=OFFICIAL,
            payload={
                "effective_date": effective,
                "ticker": t,
                "documents": docs,
                "document_count": len(docs),
                "url": url_used,
                "structured_filings": payload_obj.get("structured_filings"),
                "note": payload_obj.get("note"),
            },
            effective_date=effective,
            checksum=file_rec["checksum"],
            mode=mode,
            downloaded_files=[file_rec],
            confidence=0.85 if mode.startswith("live") else 0.75,
        )
        store.put_raw(SOURCE_ID, t, env)
        store.update_collector_health(
            COLLECTOR_ID,
            source=SOURCE_ID,
            version=COLLECTOR_ID,
            frequency="event_driven",
            retry_policy=DEFAULT_RETRY,
            last_success=store.utc_now(),
            last_checksum=file_rec["checksum"],
            success_count=(store.get_collector_health(COLLECTOR_ID).get("success_count") or 0) + 1,
            downloaded_files=[file_rec.get("path")],
            metadata={"ticker": t, "document_count": len(docs), "mode": mode},
        )
        return env
    except Exception as exc:  # noqa: BLE001
        fb = fallback_to_snapshot(
            collector_id=COLLECTOR_ID, source_id=SOURCE_ID, entity=t, reason=str(exc)[:200]
        )
        store.update_collector_health(
            COLLECTOR_ID,
            source=SOURCE_ID,
            last_failure=store.utc_now(),
            failure_count=(store.get_collector_health(COLLECTOR_ID).get("failure_count") or 0) + 1,
            last_error=str(exc)[:200],
        )
        return fb or {
            "ok": False,
            "collector_id": COLLECTOR_ID,
            "source_id": SOURCE_ID,
            "official_source": OFFICIAL,
            "entity": t,
            "reason": "collect_failed",
            "error": str(exc)[:240],
            "fixture": False,
            "fabricated": False,
            "transparent_insufficiency": True,
        }
