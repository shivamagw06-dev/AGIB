# AGI Intelligence Engine

Hybrid multi-agent research service for Agarwal Global Investments.

## Role

- **Node AGIB** remains the product gateway, cache, auth, and schedulers.
- **This engine** owns Research Director orchestration, analyst agents, evidence/confidence/citation, CIO synthesis, and memory.

Frontend must never call this service directly. Use Node `/api/intelligence/*`.

## Quick start

```bash
cd intelligence-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

Health: `GET http://127.0.0.1:8100/v1/health`

## Auth

Send `Authorization: Bearer $INTELLIGENCE_ENGINE_TOKEN` (or `X-AGI-Intelligence-Token`).

## Create a run

```bash
curl -sS -X POST http://127.0.0.1:8100/v1/research/runs \
  -H "Authorization: Bearer dev-intelligence-token" \
  -H "Content-Type: application/json" \
  -d '{"desk":"smoke"}'
```

CIO morning desk:

```bash
curl -sS -X POST http://127.0.0.1:8100/v1/research/runs \
  -H "Authorization: Bearer dev-intelligence-token" \
  -H "Content-Type: application/json" \
  -d '{"desk":"cio_morning"}'
```

## Architecture

Research Director plans and invokes analysts → Evidence/Confidence/Citation/Debate engines → Chief Investment Officer synthesizes the final report only.

Agents read **AGIB Node cached APIs only** (no direct third-party market API calls).

### Architecture v1.0.1 contracts (WBS CON-001)

- EngineState SSOT: `contracts/v1/engine_state.schema.json` (pointer: `contracts/v1/CANONICAL.json`)
- Fixtures: `contracts/v1/fixtures/`
- ORCH control plane package: `app/orch/` (Document ID `ORCH`; distinct from `app/orchestration` Research Director and from E00 Layer 5 / E10)
- ORCH status: `GET /v1/orch/status`

### WS02 Market Data Platform (WBS DATA-001–005)

- Package: `app/market_data/` — provider abstraction, rate limit, cache, retry, circuit breaker, failover
- Providers: IndianAPI, Finnhub, FMP (pluggable via registry)
- Engines must consume canonical objects from `MarketDataClient` only
- Health: `GET /v1/market-data/health`

### WS03 Feature Registry (WBS FEAT-001–005)

- Package: `app/features/` — metadata registry, calculator registry, dependency graph, calculation scheduler, PIT store, cache, versioning, health/metrics
- Categories: `TECH_`, `VOL_`, `MACRO_`, `FUND_`, `UNIV_`; external stubs for `OPTIONS_`, `SENT_`, `EVENT_`, `RVAL_`
- Engines must consume Feature Registry outputs; they must not compute RSI/EMA/ATR/etc. internally
- Health: `GET /v1/features/health`
- Scheduler: `GET /v1/features/schedule/frequencies`, `GET /v1/features/schedule/plan`
