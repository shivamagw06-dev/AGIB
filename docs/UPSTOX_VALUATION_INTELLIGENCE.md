# Upstox Valuation Integration & Institutional Valuation Intelligence v2.0

## Pipeline

```
Upstox Fundamentals (ISIN key-ratios)
        ↓
DQIV gateway
        ↓
warehouse.valuation_ratios  (append-only long format)
        ↓
warehouse.historical_valuation  (daily PE/PB/EV pivot, source=upstox)
        ↓
Unified Valuation Engine
        ↓
Terminal · Market Intelligence · Hedge Fund · Ask
```

No frontend calls Upstox.

## Provider-owned ratios

From `GET /fundamentals/{isin}/key-ratios`:

| Ratio | Stored as |
|-------|-----------|
| P/E | `pe` |
| P/B | `pb` |
| ROA | `roa` |
| ROE | `roe` |
| ROCE | `roce` |
| EV/EBITDA | `ev_ebitda` |

Each row stores **company_value** and **sector_value** (Upstox sector benchmark).

## AGI still computes

Market cap, enterprise value, price/sales, EV/sales, dividend yield, historical median/percentile/rank, relative score, valuation health, research intelligence.

## Engine preference

`valuation_engine.engine.compute` overlays Upstox ratios before derivation. If Upstox supplies PE, CMP÷EPS is **not** used.

## Daily schedule

| Time (IST) | Job |
|------------|-----|
| 18:05 | FII/DII institutional flow |
| **18:15** | **Upstox key-ratios → valuation_ratios** |
| ~18:45 | Warehouse refresh |

Manual: `POST /api/market/upstox-valuation-ratios/refresh`

## API

| Method | Path |
|--------|------|
| GET | `/v1/valuation-ratios/health` |
| GET | `/v1/valuation-ratios/coverage` |
| GET | `/v1/valuation-ratios/company/{symbol}` |
| POST | `/v1/valuation-ratios/ingest` |

BFF: `/api/intelligence/valuation-ratios/*`
