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

### ORCH Layer 2 Feature Builds (WBS ORCH-003–005)

- Package: `app/orch/l2/` — dirty tracking, build queue, dependency scheduler, feature build ledger, ready events
- Flow: MarketDataClient publish → ORCH dirty detection → impacted subgraph → Feature Registry recompute → cache/store → ready event
- Engines must not request recalculation; they only read FeatureSnapshots
- APIs: `GET /v1/orch/l2/health`, `POST /v1/orch/l2/trigger`, `POST /v1/orch/l2/drain`, `GET /v1/orch/l2/builds`

### E01 Macro & Regime Engine P0 (WBS E01-001–005)

- Package: `app/engines/e01/` — Feature Builder, threshold classifiers, MacroScore, sizing, EngineState builder
- Inputs: Feature Registry / FeatureSnapshots only (no provider payloads, no polling)
- Outputs: canonical EngineState (`engine_state.schema.json`) with E01 metadata (axes, primary_regime, size_multiplier, …)
- Flags: `E01_P0=true`, `E01_HMM=false`, `E01_ML=false`
- ORCH: passive L2 ready-event consumer (`E01_MACRO` node)
- APIs: `GET /v1/e01/state`, `GET /v1/e01/history`, `GET /v1/e01/health`

### E14 Risk & Crowding Overlay P0 (WBS E14-001–005)

- Package: `app/engines/e14/` — Risk Feature Builder, rule-based taxonomy/risk_score, sizing/conf adj, E14Assessment, EngineState
- Inputs: Feature Registry + E01State only (no MarketDataClient, no polling)
- Outputs: canonical EngineState + E14Assessment; fail-closed without E01
- Flags: `E14_P0=true`, `E14_ML=false`, `E14_BAYES=false`
- ORCH: passive consumer of FeatureSnapshot + E01State (`E14_FIRM_PRIOR` / `E14_ASSESS`)
- APIs: `GET /v1/e14/state`, `GET /v1/e14/history`, `GET /v1/e14/health`
