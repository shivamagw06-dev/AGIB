"""RBI DBIE macro collector — key policy/credit series as primitives."""

from __future__ import annotations

import json
import ssl
from pathlib import Path
from typing import Any
from urllib.request import build_opener, HTTPSHandler, Request

from live_data import store
from live_data.collectors.base import collector_envelope, fallback_to_snapshot, run_with_retry
from live_data.schema import DEFAULT_RETRY

COLLECTOR_ID = "lidi_rbi_dbie_v1"
SOURCE_ID = "rbi_dbie"
OFFICIAL = "Reserve Bank of India DBIE"
SAMPLES = Path(__file__).resolve().parents[1] / "samples"

DBIE_URLS = (
    "https://dbie.rbi.org.in/DBIE/#/dbie/home",
    "https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx",
)


def collect_rbi_dbie(
    *,
    injected_json: dict[str, Any] | str | None = None,
    allow_recorded_sample: bool = False,
) -> dict[str, Any]:
    mode = "live"
    payload_obj = None
    raw = None
    url_used = None
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
                nonlocal url_used
                # DBIE often has brittle TLS; try default then unverified for connectivity probe only.
                last = None
                ctx_default = ssl.create_default_context()
                for url in DBIE_URLS:
                    for ctx in (ctx_default, ssl._create_unverified_context()):  # noqa: S323 — documented fallback
                        try:
                            opener = build_opener(HTTPSHandler(context=ctx))
                            req = Request(
                                url,
                                headers={"User-Agent": "Mozilla/5.0 (compatible; AGIB-LIDI/1.0)", "Accept": "*/*"},
                            )
                            with opener.open(req, timeout=25) as resp:
                                data = resp.read()
                            url_used = url
                            # Landing HTML is not a series export — signal structured-data gap
                            if b"repo" not in data.lower() and b"{" not in data[:1]:
                                raise RuntimeError("rbi_dbie_no_structured_series_export")
                            return data
                        except Exception as exc:  # noqa: BLE001
                            last = exc
                raise RuntimeError(f"rbi_dbie_fetch_failed:{last}")

            try:
                policy = {"max_attempts": 1, "backoff_seconds": [0]} if allow_recorded_sample else DEFAULT_RETRY
                raw = run_with_retry(_fetch, retry_policy=policy)
                # If HTML, cannot parse series → raise to snapshot/sample path
                if raw[:1] != b"{":
                    raise RuntimeError("rbi_dbie_html_without_json_series")
                payload_obj = json.loads(raw.decode("utf-8"))
            except Exception as live_exc:
                if allow_recorded_sample:
                    sample = SAMPLES / "rbi_dbie_key_rates.json"
                    mode = "recorded_sample"
                    raw = sample.read_bytes()
                    payload_obj = json.loads(raw.decode("utf-8"))
                    url_used = str(sample)
                else:
                    fb = fallback_to_snapshot(
                        collector_id=COLLECTOR_ID,
                        source_id=SOURCE_ID,
                        entity="LATEST",
                        reason=str(live_exc)[:200],
                    )
                    store.update_collector_health(
                        COLLECTOR_ID,
                        source=SOURCE_ID,
                        last_failure=store.utc_now(),
                        failure_count=(store.get_collector_health(COLLECTOR_ID).get("failure_count") or 0) + 1,
                        last_error=str(live_exc)[:200],
                        version=COLLECTOR_ID,
                        frequency="daily_to_weekly",
                        retry_policy=DEFAULT_RETRY,
                    )
                    return fb or {
                        "ok": False,
                        "collector_id": COLLECTOR_ID,
                        "source_id": SOURCE_ID,
                        "official_source": OFFICIAL,
                        "reason": "live_unavailable_no_snapshot",
                        "error": str(live_exc)[:240],
                        "fixture": False,
                        "fabricated": False,
                        "transparent_insufficiency": True,
                    }

        assert payload_obj is not None and raw is not None
        series = list(payload_obj.get("series") or [])
        # Normalize UNKNOWN qualitative nulls
        for s in series:
            if s.get("value") is None and s.get("metric") == "liquidity_stance":
                s["value"] = "UNKNOWN"
        effective = payload_obj.get("effective_date")
        file_rec = store.put_raw_file(SOURCE_ID, "rbi_dbie.json", raw, meta={"mode": mode, "url": url_used})
        env = collector_envelope(
            collector_id=COLLECTOR_ID,
            source_id=SOURCE_ID,
            official_source=OFFICIAL,
            payload={"effective_date": effective, "series": series, "url": url_used},
            effective_date=effective,
            checksum=file_rec["checksum"],
            mode=mode,
            downloaded_files=[file_rec],
            confidence=0.9 if mode == "live" else 0.75,
        )
        store.put_raw(SOURCE_ID, "LATEST", env)
        store.update_collector_health(
            COLLECTOR_ID,
            source=SOURCE_ID,
            version=COLLECTOR_ID,
            frequency="daily_to_weekly",
            retry_policy=DEFAULT_RETRY,
            last_success=store.utc_now(),
            last_checksum=file_rec["checksum"],
            success_count=(store.get_collector_health(COLLECTOR_ID).get("success_count") or 0) + 1,
            downloaded_files=[file_rec.get("path")],
            metadata={"series_count": len(series), "mode": mode},
        )
        return env
    except Exception as exc:  # noqa: BLE001
        fb = fallback_to_snapshot(
            collector_id=COLLECTOR_ID, source_id=SOURCE_ID, entity="LATEST", reason=str(exc)[:200]
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
            "reason": "collect_failed",
            "error": str(exc)[:240],
            "fixture": False,
            "fabricated": False,
            "transparent_insufficiency": True,
        }
