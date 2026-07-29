# FSE-01 — Financial Statements Engine

Canonical financial warehouse for AGIB.

**Spec:** [`docs/FSE_01_FINANCIAL_STATEMENTS_ENGINE.md`](../../docs/FSE_01_FINANCIAL_STATEMENTS_ENGINE.md)

## What this is

Institutional financial data platform — acquire, validate, normalize, version, and publish statements.

**Not** a scraper script, AI summarizer, or BUY/SELL engine.

## Architecture

```text
Official Sources → Raw Evidence → Extraction → Normalization
  → Canonical → Validation → Version Control → Warehouse → Derived → Consumers
```

P2.1 `earnings_intelligence` is the NSE XBRL **extraction adapter** during migration.
New consumers must read through FSE — not bypass to parsers.

## CLI

```bash
export PYTHONPATH=.
python -m financial_statements_engine --health
python -m financial_statements_engine --dashboard
python -m financial_statements_engine --registry
python -m financial_statements_engine TCS
python -m financial_statements_engine TCS --publish
```

## APIs

- `GET /v1/financial-statements/health`
- `GET /v1/financial-statements/dashboard`
- `GET /v1/financial-statements/{ticker}`
- `POST /v1/financial-statements/ingest`

## Frozen surfaces

Constitution · Governance Spec · Decision Engine formulas · Gate thresholds · Evaluation Lab · IAT · Mission Control contracts
