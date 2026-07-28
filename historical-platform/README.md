# AGI Historical Intelligence Platform (HIP)

**Phase 8** — permanent historical memory for institutional reasoning across decades.

| Phase | Role |
|---|---|
| Phase 6 (KAIP) | Live knowledge |
| **Phase 8 (HIP)** | Historical knowledge |

## Sprint 8.1 — Historical Acquisition Platform (HAP)

Bulk historical ingestion → validate → normalize → resolve → versioned Historical Knowledge Store → retrieval APIs.

Ask / Intelligence Engine must retrieve history **without** calling Yahoo, NSE, BSE, or Company IR.

## Contracts

- [`docs/HAP_PLATFORM_CONTRACT.md`](docs/HAP_PLATFORM_CONTRACT.md)
- [`docs/HISTORICAL_COVERAGE_POLICY.md`](docs/HISTORICAL_COVERAGE_POLICY.md)

## Pipeline

```text
Sources → Historical Collectors → Raw Historical Archive
→ Validation → Canonical Normalizer → Entity Resolution
→ Historical Knowledge Builder → Historical Knowledge Store
→ Historical Retrieval API
```

## Collectors

- `YahooHistoricalCollector` — OHLCV, financials, dividends, splits, profile, news, analyst tips  
- `NSEHistoricalCollector` — bhavcopy, announcements, actions, index constituents  
- `BSEHistoricalCollector` — announcements, corporate actions  
- `CompanyIRHistoricalCollector` — annual/quarterly reports, presentations, transcripts, ESG, governance  

## Coverage policy

Explicit targets (daily OHLCV max history, quarterly/annual financials max history, full corporate actions, retain every IR report, …). Completeness scored per company/category.

## Run locally

```bash
cd historical-platform
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
HIP_LIVE_COLLECTORS=false uvicorn app.main:app --port 8092
```

Bootstrap (ops only):

```bash
curl -X POST http://127.0.0.1:8092/v1/internal/bootstrap
curl 'http://127.0.0.1:8092/v1/historical/company/INFY/revenue?from_period=FY2015&to_period=FY2025'
```

## Tests

```bash
cd historical-platform && pytest -q
```

## Boundary

Historical store is append-only and separate from live KAIP. Corrections create new versions. Retrieval APIs always return `providers_queried: []`.
