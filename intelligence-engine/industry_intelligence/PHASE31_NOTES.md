# Phase 3.1 — Industry Intelligence Engine

**Status:** Build complete · Acceptance = 100% · Ask/KUL **not wired**  
**Depends on:** AGI Core v1.0 (extend only — do not modify Core)  
**Version:** `3.1.0`

## Discipline

```
Build → Acceptance Test → Integration → Production Validation → Freeze
```

This PR stops after **Acceptance = 100%**. Module 14 (Ask/KUL provider registration) is intentionally deferred.

## What shipped

Package: `intelligence-engine/industry_intelligence/`

| Module | Role |
|--------|------|
| Industry Registry | 36 first-class industries + aliases |
| Industry DNA | Canonical object (economics, KPIs, valuation, regulation, competition, cycle, risks, graph) |
| KPI Engine | Deterministic industry KPIs with definition / ranges / relationships |
| Economics Engine | Causal why-margins / ROIC / leverage / WC / valuation |
| Cycle Engine | Primary cycle + lifecycle + macro sensitivity |
| Regulation Engine | Regulators + regulatory risks |
| Valuation Engine | Industry-specific methods (never universal) |
| Competition Engine | Structure + Porter forces |
| Risk Engine | Weighted industry risks |
| Industry Graph | Customers / suppliers / adjacent / substitutes / capital allocation |
| Cross-Industry | Deterministic pedagogy answers (P/B, EV/Sales, low airline ROIC, etc.) |

REST (engine-only):

- `GET /v1/industry-intelligence/health`
- `GET /v1/industry-intelligence/dashboard`
- `POST /v1/industry-intelligence/analyse`
- `GET /v1/industry-intelligence/industry/{industry_key}`
- `GET /v1/industry-intelligence/industry/{industry_key}/kpi/{kpi_key}`

Acceptance:

- `ask_product_test/industry_intelligence_acceptance_v1.py` — 200 questions
- Runner: `ask_product_test/run_industry_intelligence_acceptance_v1.py`
- Gate: **100%** before Ask integration

## Industry DNA (canonical)

Every industry exposes a structured DNA object consumed later by Business / Investment / Portfolio Intelligence — not duplicated.

```
Identity · Economics · KPIs · Value/Cost/Margin drivers · Capital intensity
Working capital · Cash conversion · Regulation · Competition · Valuation
Lifecycle · Risks · Macro sensitivity · Graph relationships
```

## Explicit non-goals (this PR)

- No KUL provider registration
- No Ask router / soft-slice wiring (`ASK_WIRED = False`)
- No Core module edits
- No LLM summaries

## Next (after merge)

1. Register `industry_intelligence` provider inside KUL  
2. Business Intelligence consumes Industry DNA (not vice versa)  
3. Production validation stack → Freeze Phase 3.1
