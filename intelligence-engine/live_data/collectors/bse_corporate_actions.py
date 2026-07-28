"""BSE Corporate Actions collector."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Any

from live_data import store
from live_data.collectors.base import collector_envelope, fallback_to_snapshot, http_get, run_with_retry
from live_data.schema import DEFAULT_RETRY

COLLECTOR_ID = "lidi_bse_corporate_actions_v1"
SOURCE_ID = "bse_corporate_actions"
OFFICIAL = "BSE India"
SAMPLES = Path(__file__).resolve().parents[1] / "samples"

# BSE corporate actions download endpoints (public pages; format may vary).
BSE_URLS = (
    "https://www.bseindia.com/corporates/corporate_act.aspx",
    "https://api.bseindia.com/BseIndiaAPI/api/DefaultData/GetData",
)


def collect_bse_corporate_actions(
    *,
    injected_csv: str | bytes | None = None,
    allow_recorded_sample: bool = False,
) -> dict[str, Any]:
    mode = "live"
    text = None
    raw = None
    url_used = None
    try:
        if injected_csv is not None:
            mode = "injected"
            raw = injected_csv.encode("utf-8") if isinstance(injected_csv, str) else injected_csv
            text = raw.decode("utf-8", errors="replace")
        else:
            def _fetch() -> bytes:
                nonlocal url_used
                last = None
                for url in BSE_URLS:
                    try:
                        data = http_get(
                            url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (compatible; AGIB-LIDI/1.0)",
                                "Accept": "text/html,application/json,*/*",
                                "Referer": "https://www.bseindia.com/",
                            },
                            timeout=25,
                        )
                        url_used = url
                        return data
                    except Exception as exc:  # noqa: BLE001
                        last = exc
                raise RuntimeError(f"bse_actions_fetch_failed:{last}")

            try:
                policy = {"max_attempts": 1, "backoff_seconds": [0]} if allow_recorded_sample else DEFAULT_RETRY
                raw = run_with_retry(_fetch, retry_policy=policy)
                text = raw.decode("utf-8", errors="replace")
                # If HTML landing page without CSV, treat as unstructured → fail to sample/snapshot
                if "<html" in text.lower() and "security code" not in text.lower():
                    raise RuntimeError("bse_actions_html_without_tabular_export")
            except Exception as live_exc:
                if allow_recorded_sample:
                    sample = SAMPLES / "bse_corporate_actions.csv"
                    mode = "recorded_sample"
                    raw = sample.read_bytes()
                    text = raw.decode("utf-8")
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
                        frequency="daily",
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

        assert text is not None and raw is not None
        actions, effective = _parse_actions_csv(text)
        file_rec = store.put_raw_file(SOURCE_ID, "corporate_actions.csv", raw, meta={"mode": mode, "url": url_used})
        env = collector_envelope(
            collector_id=COLLECTOR_ID,
            source_id=SOURCE_ID,
            official_source=OFFICIAL,
            payload={"effective_date": effective, "actions": actions, "action_count": len(actions), "url": url_used},
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
            frequency="daily",
            retry_policy=DEFAULT_RETRY,
            last_success=store.utc_now(),
            last_checksum=file_rec["checksum"],
            success_count=(store.get_collector_health(COLLECTOR_ID).get("success_count") or 0) + 1,
            downloaded_files=[file_rec.get("path")],
            metadata={"action_count": len(actions), "mode": mode},
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


def _parse_actions_csv(text: str) -> tuple[list[dict[str, Any]], str | None]:
    # Map common BSE names → tickers for Track-1 bridge (limited dictionary)
    NAME_MAP = {
        "INFOSYS LTD": "INFY",
        "TCS LTD": "TCS",
        "RELIANCE INDUSTRIES LTD": "RELIANCE",
    }
    reader = csv.DictReader(io.StringIO(text))
    actions = []
    effective = None
    for raw in reader:
        row = {}
        for k, v in raw.items():
            if k is None:
                continue
            if isinstance(v, list):
                v = v[0] if v else ""
            row[str(k).strip()] = str(v or "").strip()
        name = row.get("Security Name") or row.get("SecurityName") or ""
        purpose = row.get("Purpose") or row.get("purpose") or ""
        ex = row.get("Ex Date") or row.get("ExDate") or ""
        code = row.get("Security Code") or row.get("SecurityCode")
        sym = NAME_MAP.get(name.upper()) or NAME_MAP.get(name) or None
        if not purpose:
            continue
        ed = _parse_date(ex)
        if ed and not effective:
            effective = ed
        actions.append(
            {
                "symbol": sym,
                "security_code": code,
                "security_name": name,
                "purpose": purpose,
                "ex_date": ed,
                "record_date": _parse_date(row.get("Record Date") or ""),
                "effective_date": ed,
                "action_type": _classify(purpose),
            }
        )
    return actions, effective


def _parse_date(s: str) -> str | None:
    s = str(s or "").strip()
    if not s:
        return None
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            continue
    return None


def _classify(purpose: str) -> str:
    p = purpose.lower()
    if "split" in p:
        return "split"
    if "bonus" in p:
        return "bonus"
    if "right" in p:
        return "rights"
    if "dividend" in p or "div " in p:
        return "dividend"
    if "buyback" in p:
        return "buyback"
    return "corporate_action"
