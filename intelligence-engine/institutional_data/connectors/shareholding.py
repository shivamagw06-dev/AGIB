"""Shareholding connector — historical ownership (Promoter/FII/DII/MF/Public/Pledged)."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from typing import Any

from institutional_data.connectors.base import Connector, ConnectorResult


class ShareholdingConnector(Connector):
    connector_id = "hd_shareholding_v1"
    source_id = "shareholding"
    official_source = "NSE / BSE shareholding patterns"

    def collect(self, **kwargs: Any) -> ConnectorResult:
        entity = str(kwargs.get("entity") or kwargs.get("ticker") or "").upper()
        t0 = time.time()
        if not entity:
            return ConnectorResult(ok=False, connector_id=self.connector_id, source_id=self.source_id, error="entity_required")

        records: list[dict[str, Any]] = []
        errors: list[str] = []
        mode = "live"
        path = None

        # Primary: NSE corporate shareholding API
        try:
            rows, path = self._nse_shareholding(entity)
            records.extend(rows)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"nse:{str(exc)[:120]}")

        # Secondary: BSE HTML/pattern probe
        if not records:
            try:
                rows, path2 = self._bse_shareholding(entity)
                records.extend(rows)
                path = path or path2
            except Exception as exc:  # noqa: BLE001
                errors.append(f"bse:{str(exc)[:120]}")

        # Injected for tests
        if kwargs.get("injected"):
            mode = "injected"
            records = list(kwargs["injected"])

        ok = bool(records)
        return ConnectorResult(
            ok=ok,
            connector_id=self.connector_id,
            source_id=self.source_id,
            records=records,
            mode=mode,
            error=None if ok else (errors[0] if errors else "shareholding_unavailable"),
            diagnostics={"entity": entity, "errors": errors, "parse_path": path, "latency_ms": int((time.time() - t0) * 1000)},
            coverage_pct=100.0 if ok else 0.0,
            repair_items=[]
            if ok
            else [{"company": entity, "reason": "missing_shareholding", "connector": self.connector_id, "priority": 2}],
        )

    def validate(self, records: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        if not records:
            return {"ok": False, "reason": "empty"}
        bad = []
        for r in records:
            total = sum(
                float(r.get(k) or 0)
                for k in ("promoter", "fii", "dii", "mutual_funds", "public")
            )
            # Allow rounding slack; pledged is subset of promoter often
            if total > 105 or total < 80:
                bad.append({"period": r.get("period"), "total": total, "reason": "ownership_sum_out_of_range"})
        return {"ok": len(bad) == 0, "rejected": len(bad), "accepted": len(records) - len(bad), "failures": bad[:20]}

    def normalize(self, records: list[dict[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
        out = []
        for r in records:
            out.append(
                {
                    "entity": str(r.get("entity") or kwargs.get("entity") or "").upper(),
                    "period": str(r.get("period")),
                    "period_end": str(r.get("period_end") or r.get("period"))[:10],
                    "promoter": _pct(r.get("promoter")),
                    "fii": _pct(r.get("fii") or r.get("fpi")),
                    "dii": _pct(r.get("dii")),
                    "mutual_funds": _pct(r.get("mutual_funds") or r.get("mf")),
                    "public": _pct(r.get("public")),
                    "pledged": _pct(r.get("pledged") or r.get("promoter_pledged")),
                    "source": r.get("source") or "shareholding_connector",
                }
            )
        return out

    def store(self, records: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        from knowledge_factory.historical_depth import store as hd_store
        from knowledge_factory.historical_depth.schema import pit_record

        entity = str(kwargs.get("entity") or (records[0].get("entity") if records else "")).upper()
        pits = []
        for r in records:
            pe = r.get("period_end") or r.get("period")
            pits.append(
                pit_record(
                    entity=entity,
                    kind="shareholding",
                    period=str(r.get("period")),
                    period_end=str(pe)[:10],
                    available_from=str(pe)[:10],
                    payload={
                        "promoter": r.get("promoter"),
                        "fii": r.get("fii"),
                        "dii": r.get("dii"),
                        "mutual_funds": r.get("mutual_funds"),
                        "public": r.get("public"),
                        "pledged": r.get("pledged"),
                    },
                    source="shareholding_connector",
                    confidence=0.9,
                )
            )
        hd_store.put_series("shareholding", entity, pits)
        return {"written": len(pits), "entity": entity}

    def coverage(self, **kwargs: Any) -> dict[str, Any]:
        from knowledge_factory.historical_depth import store as hd_store
        from knowledge_factory.historical_depth.universe_priority import supported_universe

        u = kwargs.get("entities") or supported_universe()
        n = len(u) or 1
        covered = sum(1 for e in u if (hd_store.get_series("shareholding", e) or {}).get("records"))
        return {"connector_id": self.connector_id, "coverage_pct": round(100.0 * covered / n, 1), "covered": covered, "universe": n}

    def _nse_shareholding(self, entity: str) -> tuple[list[dict[str, Any]], str]:
        from live_data.collectors.base import nse_session_opener
        from urllib.request import Request

        opener = nse_session_opener()
        url = f"https://www.nseindia.com/api/corporate-share-holdings-master?index=equities&symbol={entity}"
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AGIB-LIDI/1.0)",
                "Accept": "application/json",
                "Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={entity}",
            },
        )
        with opener.open(req, timeout=30) as resp:
            raw = resp.read()
        data = json.loads(raw.decode("utf-8"))
        rows = data if isinstance(data, list) else (data.get("data") or data.get("shareholding") or [])
        out = []
        for r in rows if isinstance(rows, list) else []:
            if not isinstance(r, dict):
                continue
            period = r.get("date") or r.get("period") or r.get("asOnDate") or ""
            out.append(
                {
                    "entity": entity,
                    "period": str(period)[:10],
                    "period_end": str(period)[:10],
                    "promoter": r.get("promoterPledgedPercentage") and r.get("totalPromoterHolding") or r.get("promoter") or r.get("totalPromoterHolding"),
                    "fii": r.get("fii") or r.get("foreignInstitutions") or r.get("FII"),
                    "dii": r.get("dii") or r.get("domesticInstitutions") or r.get("DII"),
                    "mutual_funds": r.get("mutualFunds") or r.get("mf"),
                    "public": r.get("public") or r.get("retailAndOthers"),
                    "pledged": r.get("promoterPledgedPercentage") or r.get("pledged"),
                    "source": "nse_api",
                }
            )
        # Alternate NSE endpoint shape
        if not out and isinstance(data, dict):
            for key in ("promoterHolding", "publicHolding", "institutionalHolding"):
                if key in data:
                    # Single snapshot
                    out.append(
                        {
                            "entity": entity,
                            "period": datetime.now(timezone.utc).date().isoformat(),
                            "period_end": datetime.now(timezone.utc).date().isoformat(),
                            "promoter": _dig(data, "promoterHolding", "total"),
                            "fii": _dig(data, "institutionalHolding", "fii"),
                            "dii": _dig(data, "institutionalHolding", "dii"),
                            "mutual_funds": _dig(data, "institutionalHolding", "mf"),
                            "public": _dig(data, "publicHolding", "total"),
                            "pledged": _dig(data, "promoterHolding", "pledged"),
                            "source": "nse_api_alt",
                        }
                    )
                    break
        return out, "nse_api"

    def _bse_shareholding(self, entity: str) -> tuple[list[dict[str, Any]], str]:
        from live_data.collectors.base import http_get

        # Soft probe — extract percentages if page renders server-side
        url = f"https://www.bseindia.com/stock-share-price/shareholding-pattern/{entity.lower()}/"
        try:
            raw = http_get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AGIB-LIDI/1.0)", "Referer": "https://www.bseindia.com/"},
                timeout=25,
            )
        except Exception:
            # Generic corporate page
            raw = http_get(
                "https://www.bseindia.com/corporates/Sharehold_Searchnew.aspx",
                headers={"User-Agent": "Mozilla/5.0 (compatible; AGIB-LIDI/1.0)"},
                timeout=25,
            )
        text = raw.decode("utf-8", errors="replace")
        promoter = _find_pct(text, r"Promoter[^0-9]{0,40}([0-9]+(?:\.[0-9]+)?)\s*%")
        fii = _find_pct(text, r"(?:FII|FPI)[^0-9]{0,40}([0-9]+(?:\.[0-9]+)?)\s*%")
        dii = _find_pct(text, r"DII[^0-9]{0,40}([0-9]+(?:\.[0-9]+)?)\s*%")
        public = _find_pct(text, r"Public[^0-9]{0,40}([0-9]+(?:\.[0-9]+)?)\s*%")
        mf = _find_pct(text, r"Mutual\s*Fund[^0-9]{0,40}([0-9]+(?:\.[0-9]+)?)\s*%")
        pledged = _find_pct(text, r"Pledg[^0-9]{0,40}([0-9]+(?:\.[0-9]+)?)\s*%")
        if promoter is None and fii is None:
            return [], "bse_html_empty"
        today = datetime.now(timezone.utc).date().isoformat()
        return (
            [
                {
                    "entity": entity,
                    "period": today,
                    "period_end": today,
                    "promoter": promoter,
                    "fii": fii,
                    "dii": dii,
                    "mutual_funds": mf,
                    "public": public,
                    "pledged": pledged,
                    "source": "bse_html",
                }
            ],
            "bse_html",
        )


def _pct(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return round(float(v), 4)
    except Exception:
        return None


def _find_pct(text: str, pattern: str) -> float | None:
    m = re.search(pattern, text, re.I)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _dig(d: dict[str, Any], *keys: str) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur
