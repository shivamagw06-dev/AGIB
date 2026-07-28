# AGI Knowledge Acquisition Platform (KAIP)

Standalone always-on service that continuously ingests institutional data, converts it into AGI’s canonical knowledge model, and publishes Knowledge Objects to the Intelligence Engine.

**Sprint 6.1** acquisition · **6.2** IKO · **6.3** ILE · **6.4** KRIG. KAIP does **not** perform reasoning.

## Platform contracts

- Acquisition: [`docs/KAIP_PLATFORM_CONTRACT.md`](docs/KAIP_PLATFORM_CONTRACT.md)
- Knowledge model: [`docs/IKO_PLATFORM_CONTRACT.md`](docs/IKO_PLATFORM_CONTRACT.md)
- Learning engine: [`docs/ILE_PLATFORM_CONTRACT.md`](docs/ILE_PLATFORM_CONTRACT.md)
- Retrieval gateway: [`docs/KRIG_PLATFORM_CONTRACT.md`](docs/KRIG_PLATFORM_CONTRACT.md)

## Pipeline

```text
Sources → Scheduler → Collectors → Raw Event Store → Validation
→ Canonical Normalizer → Entity Resolution → Knowledge Object Builder
→ Relationship Builder → Change Detection → Publisher → Intelligence Engine
```

## Collectors (only these)

- `YahooCollector` (30s)
- `NSEAnnouncementCollector` (30s)
- `NSEBhavcopyCollector` (daily)
- `BSECorporateActionCollector` (daily)
- `CompanyIRCollector` (daily)

## Institutional Knowledge Objects (ten)

`CompanyProfile` · `MarketSnapshot` · `FinancialStatement` · `CorporateEvent` · `CorporateAction` · `Ownership` · `AnalystConsensus` · `NewsEvent` · `SectorKnowledge` · `MarketKnowledge`

## Internal APIs

```text
GET /v1/knowledge/company/{symbol}
GET /v1/knowledge/market/{symbol}
GET /v1/knowledge/events/{symbol}
GET /v1/knowledge/financials/{symbol}
GET /v1/knowledge/learning/{symbol}
GET /healthz
GET /readyz
```

## Run locally

```bash
cd knowledge-platform
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
KAIP_SCHEDULER=false KAIP_LIVE_COLLECTORS=false uvicorn app.main:app --port 8091
```

## Tests

```bash
cd knowledge-platform
pip install -r requirements.txt
pytest -q
```

## Boundary

Intelligence Engine retrieves published Knowledge Objects via internal APIs.  
It must never know Yahoo / NSE / BSE / Company IR exist.
