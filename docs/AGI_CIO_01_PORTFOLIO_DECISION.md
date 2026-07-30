# CIO-01 — Institutional Portfolio Decision System

**Mission:** Transform company decisions + portfolio graph into a deterministic **InstitutionalPortfolioDecision**.

```text
Company Decisions (immutable references)
↓
Portfolio Graph (PKG-01)
↓
Portfolio Decision Engine
↓
Portfolio Calibration
↓
Allocation / Exposure Actions + Monitoring
```

A portfolio recommendation is **not** the average of company recommendations.

## Architectural invariant

- Company `InstitutionalDecision` objects are **immutable inputs**
- Portfolio decisions are **referential** — they cite `decision_id` / recommendation / confidence
- The same company intelligence can be reused across portfolios, watchlists, and clients
- CIO-01 never rewrites Axis HOLD because the book is overweight financials

## InstitutionalPortfolioDecision

Immutable, versioned. Fields include recommendation, confidence, conviction, investment posture, supporting/contradicting company decision refs, allocation actions, exposure actions, portfolio risks, monitoring plan, calibration, scorecard, diagnostics, lineage.

### Recommendations

Maintain Allocation · Increase Financials · Reduce Technology · Increase Cash · Reduce Concentration · Increase Diversification · Review Portfolio · No Action Required

## Package

`intelligence-engine/institutional_portfolio_decision/`

| Module | Role |
| --- | --- |
| `decision_engine.py` | Portfolio recommendation + rule path |
| `allocation_actions.py` | Deterministic sizing intents (e.g. 28% → 25%) |
| `exposure_actions.py` | Sector/country/liquidity/style actions |
| `calibration.py` | Portfolio-level confidence (not IDS-02) |
| `monitoring.py` | Reviews, committee items, scenario re-runs |
| `decision_validator.py` | Quality gates |
| `production.py` | Decide / get / Portfolio Command Center soft slice |

## Access

```bash
cd intelligence-engine
PYTHONPATH=. python3 -m institutional_portfolio_decision --portfolio default
```

API:

- `GET /v1/portfolio-decision/health`
- `POST /v1/portfolio-decision`
- `GET /v1/portfolio-decision/{portfolio}`

BFF: `/api/intelligence/portfolio-decision/*`

## UI

`/agi/portfolio` (Investment Office) → **Portfolio Decision** panel: recommendation, allocation/exposure changes, scorecard, monitoring, lineage.

Mission Control → **Portfolio Command Center**.

## Out of scope

Trade execution · portfolio optimisation · tax optimisation · TCA · multi-asset · LLM commentary
