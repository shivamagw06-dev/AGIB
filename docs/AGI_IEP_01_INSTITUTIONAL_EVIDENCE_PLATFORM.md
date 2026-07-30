# AGIB V1.1 — Institutional Evidence Platform (IEP-01)

## Mission

AGIB's highest priority is no longer building additional intelligence engines.

The highest priority is building an **Institutional Evidence Platform** that ensures every investment opinion is supported by complete, validated, traceable institutional evidence.

```text
Raw Data → Canonical Evidence → Company Memory → Knowledge Graph
→ Financial Intelligence → Decision Engine → Research Note

NOT

Raw Data → LLM → Research Note
```

Intelligence is a consumer of evidence — not a substitute for it.

## Design principles

1. No research without evidence.
2. No recommendation without canonical financial statements.
3. No narrative without lineage.
4. Every material claim must map to primary evidence.
5. Missing evidence must block publication.
6. Every downstream engine consumes a single canonical **InstitutionalResearchPack**.

## Package

`intelligence-engine/institutional_evidence/`

| Module | Role |
|--------|------|
| `acquisition/` | Collect institutional documents (identity metadata required) |
| `canonical/` | `CanonicalFinancialStatements` — one schema for all providers |
| `registry/` | Immutable evidence objects (hash, authority, freshness) |
| `company_memory_bridge/` | Persistent per-company institutional memory view |
| `research_pack/` | Single canonical pack for all consumers |
| `validator/` | Block if mandatory components fail |
| `readiness/` | Research Ready / Research Blocked index |
| `orchestrator/` | Ask → registry → ingest/publish → pack → research |
| `gates.py` | Soft hooks for Writer / Decision / Publishing |

## Soft gates

- **Research Writer** — cannot execute unless `ResearchPack.claim_safe == true`. Never invent revenue/EPS/EBITDA/debt/margins/ARPU/GRM/capex/valuation; write `Evidence unavailable.`
- **Decision Engine** — cannot issue BUY/SELL/OVERWEIGHT/UNDERWEIGHT unless evidence complete + statements published + readiness above threshold; otherwise `NO RECOMMENDATION` / `MONITOR`.
- **Publishing** — reject if `claim_safe == false` or Research Ready == false.

## API (engine + BFF)

Prefix: `/v1/iep/*` (BFF: `/api/intelligence/iep/*`)

- `GET /iep/health` · `/iep/status` · `/iep/center` · `/iep/phase1` · `/iep/metrics`
- `GET /iep/pack/{ticker}` · `/iep/readiness/{ticker}` · `/iep/validate/{ticker}`
- `POST /iep/orchestrate/{ticker}`
- `GET /iep/registry/{ticker}` · `/iep/canonical/{ticker}` · `/iep/memory/{ticker}`
- Writer / decision / publish gates under `/iep/gates/...`

> Note: `/v1/evidence/*` remains reserved for Institutional Evidence Retrieval (IERE).

## Phase 1 target

Complete institutional coverage for **Top 20 Indian companies** (cross-sector) before scaling to Nifty 500.

For each company: automatic acquisition, canonical statements, evidence registry, company memory, research pack, research readiness, and an institutional research note with every material claim backed by primary evidence.

## CI gates

Fail build if:

- Canonical statements contain zero periods
- Accounting identities fail
- Evidence hash missing
- Freshness exceeded
- Research Pack incomplete
- Recommendation contradiction detected
- Research generated with missing mandatory evidence

## Related fix

`financial_statements_engine/extraction/nse_xbrl.py` now accepts `quarter_history` / `annual_history` (earnings_intelligence shape) in addition to `quarters` / `annuals` — unblocking FSE extract → publish for packs that already carry XBRL-derived history.

## Mission Control

Evidence Center soft slice on Mission Control (`institutional_evidence`). Live coverage via `/iep/phase1` and `/iep/metrics`.
