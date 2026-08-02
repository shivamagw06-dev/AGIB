# Valuation Intelligence — Institutional Consensus Dashboard

**Branch:** `cursor/valuation-intelligence-dashboard-4cc0`  
**Route:** `/admin/valuation-intelligence`  
**Principle:** Capital IQ = Market Consensus · AGI = Institutional Intelligence

## Architecture

```
Admin uploads CapIQ Excel
        ↓
Parse + map columns + resolve tickers
        ↓
Preview / Validate (staged import draft)
        ↓
Publish → valuation_consensus store (versioned)
        ↓
UI + Ask AGI (KUL provider) read DB only
```

Excel is **never** the live datastore. Imports create versioned snapshots with rollback.

AGI Intelligence panels and Ask answers soft-read AGI engines separately and are **never overwritten** by CIQ fields.

## Surfaces

| Surface | Path |
|--------|------|
| Dashboard UI | `/admin/valuation-intelligence` |
| Health | `GET /v1/valuation-consensus/health` |
| Analytics | `GET /v1/valuation-consensus/analytics` |
| Rows (search/filter/sort/page) | `GET /v1/valuation-consensus/rows` |
| Company expansion | `GET /v1/valuation-consensus/company/{ticker}` |
| Import preview/validate/publish/rollback | `POST /v1/valuation-consensus/import/*` |
| Export snapshot | `GET /v1/valuation-consensus/export` |
| Node BFF | `/api/intelligence/valuation-consensus/*` |

## Ask AGI learning

KUL provider id: `valuation_consensus`

- Registered in company / business / investment / portfolio / research / valuation menus
- Hard provider for Ask short-circuit eligibility
- Facts labeled `layer: market_consensus` / `source: capital_iq_market_consensus`
- Broker Buy/Hold/Sell counts are **market observations**, never framed as AGI recommendations

## Admin workflow

1. **Import Capital IQ Excel** (or click **Load Broker Estimates** to publish the committed file)
2. **Preview Changes** (added / changed / removed) — runs automatically on file choose
3. **Validate**
4. **Publish**
5. **Rollback** to prior version if needed
6. **Export Current Snapshot**

No row-by-row editing.

## Broker Estimates source

Committed under `capital_iq_exports/`:

- `broker_estimates.xlsx` — formatted CapIQ Broker Estimates (headers cleaned; numbers unchanged)
- `broker_estimates_raw.xlsx` — original GitHub upload

Boot seed: `valuation_consensus.seed_broker_estimates.seed_if_needed` (same durability pattern as IKT CapIQ seed).

## Persistence

- Runtime default: `$KIP_DATA_DIR/valuation_consensus/` (or `VALUATION_CONSENSUS_ROOT`)
- Optional Postgres: `supabase/migrations/20260802120000_valuation_consensus.sql`

## Future (not in this PR)

- Live market prices
- Historical consensus / target revisions
- Broker consensus history
- AGI valuation overlay

## Success criteria

- Premium institutional UI (not a screener / spreadsheet)
- 5,500+ company capacity (server pagination + compact projections)
- Admin-only import/publish/rollback
- Full search / filter / sort
- AGI Intelligence panel + Ask learning
- Version history + audit trail
