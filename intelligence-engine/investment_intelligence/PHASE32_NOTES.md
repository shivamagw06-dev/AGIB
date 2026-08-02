# Phase 3.2 — Investment Intelligence Engine

**Status:** Build complete · Acceptance = 100% · Ask/KUL **not wired**  
**Depends on:** AGI Core v1.1 (extend only) + Business Intelligence + Industry DNA  
**Version:** `3.2.0`

## Discipline

```
Build → Acceptance Test → Integration → Production Validation → Freeze
```

This PR stops after **Acceptance = 100%**. Modules 11–16 (KUL integration, Founder V4, freeze) are deferred.

## Objective

Answer **"So what?"** for investors — quality, attractiveness, risks, scenarios, valuation drivers, evidence, uncertainty — **without** BUY/SELL recommendations.

## Modules shipped

| Module | Role |
|--------|------|
| Investment Thesis | Structured thesis (quality, position, risks, catalysts, unknowns) |
| Catalyst Intelligence | Positive/negative catalysts with probability, horizon, impact |
| Risk Intelligence | Typed risks with severity, mitigants, leading indicators |
| Scenario Intelligence | Bull / base / bear — **no price targets** |
| Quality Engine | 10-dimension scorecard with why / helped / hurt / unknowns |
| Valuation Intelligence | Consumes Industry DNA methods; sensitivity — no targets |
| Capital Allocation | Organic, dividends, buybacks, M&A, debt, capex evaluation |
| Evidence Confidence | High/medium/low/unknown + missing data |
| Committee Simulation | 9 roles + chair synthesis — NO BUY / NO SELL |
| Investment Graph | Canonical investment object |

## REST

- `GET /v1/investment-intelligence/health`
- `GET /v1/investment-intelligence/dashboard`
- `POST /v1/investment-intelligence/analyse`

## Acceptance

```bash
cd intelligence-engine
python3 ask_product_test/run_investment_intelligence_acceptance_v1.py
```

300 questions · gate **100%** · artifact `investment_intelligence_acceptance_v1.json`

## Explicit non-goals (this PR)

- No KUL provider registration
- No Ask wiring (`ASK_WIRED = False`)
- No BUY/SELL / price targets
- No Core modifications

## Next

1. Register `investment_intelligence` in KUL  
2. Investment Integration Acceptance (~75)  
3. Founder Evaluation V4  
4. Production validation → Freeze Phase 3.2
