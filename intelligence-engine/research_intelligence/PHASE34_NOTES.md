# Phase 3.4 — Research Intelligence Engine

**Status:** Build complete · Acceptance target 100% · Ask/KUL **not wired**  
**Depends on:** AGI Core v1.1 (extend only) + Investment Intelligence + Portfolio Intelligence  
**Version:** `3.4.0`

## Discipline

```
Build → Acceptance Test → Integration → Production Validation → Freeze
```

This PR stops after **Acceptance = 100%**. KUL integration, Founder V6, and freeze are deferred.

## Objective

Perform **institutional research** — structured memory across documents and time — not retrieval or summarization.

## Knowledge authority refinement

**Research Intelligence is the only Phase-3 layer allowed to create new long-lived research knowledge.**  
Financial / Business / Industry / Investment / Portfolio layers **consume** structured research outputs.

## Modules shipped

| Module | Role |
|--------|------|
| Research Workspace | Canonical Research Object |
| Annual Report Intelligence | Structured extracts → memory |
| Transcript Intelligence | Commentary / Q&A / guidance / pricing tracks |
| Management Intelligence | Leadership, consistency, philosophy |
| Guidance Intelligence | vs previous / consensus / actual |
| Estimate Intelligence | Consensus/revisions/gaps — **no forecasting** |
| Event Intelligence | Events linked to business/industry/investment/portfolio |
| Research Memory | Persistent conclusions, themes, histories |
| Cross-Document | One document timeline |
| Research Timeline | Chronological company intelligence |
| Quality Engine | Evidence, freshness, coverage, contradictions |
| Knowledge Evolution | Research → BI → INV → Portfolio path |
| Deep Research | Multi-year institutional synthesis |
| Executive Research Notes | Fixed communication order |

## REST

- `GET /v1/research-intelligence/health`
- `GET /v1/research-intelligence/dashboard`
- `GET /v1/research-intelligence/entities`
- `POST /v1/research-intelligence/analyse`
- `POST /v1/research-intelligence/soft_slice` (blocked while unwired)

## Acceptance

```bash
cd intelligence-engine
PYTHONPATH=. python3 ask_product_test/run_research_intelligence_acceptance_v1.py
```

400 questions · gate **100%**

## Explicit non-goals (this PR)

- No KUL provider registration
- No Ask wiring (`ASK_WIRED = False`)
- No BUY/SELL / forecasting as recommendations
- No Core modifications
- Does not replace `research_intelligence_hub` / `research_writer` soft layers

## Next

1. Register `research_intelligence` in KUL  
2. Research Integration Acceptance (~100)  
3. Founder Evaluation V6  
4. Production validation → Freeze Phase 3.4
