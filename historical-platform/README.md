# AGI Historical Intelligence Platform (HIP)

**Phase 8** — permanent historical memory for institutional reasoning across decades.

| Phase | Role |
|---|---|
| Phase 6 (KAIP) | Live knowledge |
| **Phase 8 (HIP)** | Historical knowledge |

## Sprint 8.1 — Historical Acquisition Platform (HAP)

Bulk historical ingestion → validate → normalize → resolve → versioned Historical Knowledge Store → retrieval APIs.

## Sprint 8.2 — Historical Knowledge Objects & Timeline Intelligence

Shape HKO views and build company / sector / market / macro **timelines** so Ask retrieves historical narratives, not rows.

Ask / Intelligence Engine must retrieve history **without** calling Yahoo, NSE, BSE, or Company IR.

## Contracts

- [`docs/HAP_PLATFORM_CONTRACT.md`](docs/HAP_PLATFORM_CONTRACT.md)
- [`docs/HISTORICAL_COVERAGE_POLICY.md`](docs/HISTORICAL_COVERAGE_POLICY.md)
- [`docs/HKO_TIMELINE_CONTRACT.md`](docs/HKO_TIMELINE_CONTRACT.md)
- Programme note: [`../docs/HIP_SPRINT_8_2.md`](../docs/HIP_SPRINT_8_2.md)

## Pipeline

```text
Sources → Historical Collectors → Raw Historical Archive
→ Validation → Canonical Normalizer → Entity Resolution
→ Historical Knowledge Builder (HKO) → Timeline Builder
→ Historical Knowledge Store → Historical Retrieval API
```

## Collectors

- `YahooHistoricalCollector` — OHLCV, financials, dividends, splits, profile, news, analyst tips  
- `NSEHistoricalCollector` — bhavcopy, announcements, actions, index constituents  
- `BSEHistoricalCollector` — announcements, corporate actions  
- `CompanyIRHistoricalCollector` — annual/quarterly reports, presentations, transcripts, ESG, governance  

## History APIs (8.2)

```text
GET  /v1/history/company/{symbol}
GET  /v1/history/timeline/{symbol}
GET  /v1/history/financials/{symbol}
GET  /v1/history/events/{symbol}
POST /v1/history/compare
GET  /v1/history/mission-control
```

## Run locally

```bash
cd historical-platform
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
HIP_LIVE_COLLECTORS=false uvicorn app.main:app --port 8092
```

Bootstrap (ops only — rebuilds timelines):

```bash
curl -X POST http://127.0.0.1:8092/v1/internal/bootstrap
curl http://127.0.0.1:8092/v1/history/timeline/INFY
curl -X POST http://127.0.0.1:8092/v1/history/compare \
  -H 'content-type: application/json' \
  -d '{"symbol":"INFY","as_of_period":"FY2018"}'
```

## Tests

```bash
cd historical-platform && pytest -q
```

## Boundary

Historical store is append-only and separate from live KAIP. Corrections create new versions. Timeline narratives may be regenerated; HKO facts are never overwritten. Retrieval APIs always return `providers_queried: []`.
