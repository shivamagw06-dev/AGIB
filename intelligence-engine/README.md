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

### E02 Factor & Style Engine P0 (WBS E02-001–005)

- Package: `app/engines/e02/` — Factor Feature Builder, exposure calculator, sector/universe normalisation, E02Exposure, EngineState
- P0 factors only: Momentum, LowVol, Size, Liquidity, Quality, Value
- Inputs: FeatureSnapshot + E01State + E14State only (no MarketDataClient, no polling)
- Flags: `E02_P0=true`, `E02_TIMING/ROTATION/SMART_BETA/ML=false`
- ORCH: passive Feature Ready / E01 Ready / E14 Ready consumer
- APIs: `GET /v1/e02/exposure/{symbol}`, `GET /v1/e02/history/{symbol}`, `GET /v1/e02/health`

### E03 Cross-Sectional Quant Engine P0/M0 (WBS E03-001–005)

- Package: `app/engines/e03/` — Technical Feature Adapter, `SM_AGI_TECH` (production `score_research` parity), E03Alpha, EngineState, ParityReport
- Behavioural migration only: RSI / MACD / SMA / returns / volume / range / ROC thresholds identical to `nifty500_research_engine.py`
- Inputs: FeatureSnapshot + E01State + E14State + E02Exposure only (no MarketDataClient, no polling)
- Flags: `E03_P0=true`, `E03_PARITY=true`, `E03_COMPOSITE/XS_MODE/ML=false`
- ORCH: passive Feature Ready / E01 Ready / E14 Ready / E02 Ready consumer
- APIs: `GET /v1/e03/alpha/{symbol}`, `GET /v1/e03/history/{symbol}`, `GET /v1/e03/parity`, `GET /v1/e03/health`

### L4 Composite Intelligence P0 Shadow (WBS L4-001–005)

- Package: `app/engines/l4/` — EngineState collector, evidence aggregator, conflict resolver, rule-based vote, L4Opinion, ShadowComparison
- Shadow only: never influences production; never replaces E03
- Inputs: E01State + E14State + E02Exposure + E03Alpha only (no MarketDataClient, no FeatureSnapshot)
- Flags: `L4_SHADOW=true`, `L4_PRIMARY/BAYES/ML/PROBABILITY=false`
- ORCH: passive E01 / E14 / E02 / E03 Ready consumer
- APIs: `GET /v1/l4/opinion/{symbol}`, `GET /v1/l4/history/{symbol}`, `GET /v1/l4/health`

### E10 Portfolio Construction P0 (WBS E10-001–005)

- Package: `app/engines/e10/` — Top-N selection, inverse-volatility, vol targeting, name/sector caps, cash floors, E10Portfolio validation
- Model portfolio only: no execution, OMS, broker routing, BL/MVO/HRP/ERC
- Inputs: L4Opinion + E14State + E02Exposure only
- Flags: `E10_P0=true`, `E10_OPTIMIZER/HRP/MVO=false`
- ORCH: passive L4 Ready consumer
- APIs: `GET /v1/e10/portfolio`, `GET /v1/e10/history`, `GET /v1/e10/health`

### Validation & Backtesting P0 (WBS BT-001–005)

- Package: `app/validation/` — Replay Engine, Golden Dataset Loader, Historical Engine Runner, Metrics, Dashboard payload
- Pipeline: Snapshot → E01 → E14 → E02 → E03 → L4 → E10 → Metrics (isolated instances; replay store only)
- Metrics: daily/benchmark return, hit/win rate, IC, Sharpe, Sortino, max DD, turnover, confidence calibration, bucket accuracy, parity stability
- Flags: `BACKTEST=true`, `LIVE=false`
- APIs: `POST /v1/validation/replay`, `GET /v1/validation/runs`, `GET /v1/validation/runs/{id}`, `GET /v1/validation/dashboard/{id}`, `GET /v1/validation/health`

### Continuous Research Evaluation P0 (WBS CRE-001–005)

- Package: `app/cre/` — Daily Evaluation Runner, Rolling Metrics Store, Drift Detection, Research Scorecards, Promotion Evidence, Dashboard
- Not a research/trading engine: consumes Historical Replay, Daily Shadow Runs, EngineStates, L4Opinion, E10Portfolio
- Rolling windows: 30 / 90 / 252 days (adaptive `days_used` when series shorter)
- Drift: model, confidence, feature, distribution, performance + regression alerts
- Outputs: EngineScorecard, CompositeScorecard, PromotionReport, DriftAlert, RegressionAlert
- Flags: `CRE=true`, `PROMOTION=false` (evidence-only; never promotes / no production influence)
- APIs: `POST /v1/cre/evaluate`, `GET /v1/cre/scorecards`, `GET /v1/cre/scorecards/{engine}`, `GET /v1/cre/alerts`, `GET /v1/cre/promotion`, `GET /v1/cre/dashboard`, `GET /v1/cre/health`
