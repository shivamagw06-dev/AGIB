# Sector Valuation Explorer & Industry Intelligence Terminal v1.0

**Route:** `/valuation-terminal` · `/admin/valuation-terminal`  
**Engine:** `intelligence-engine/sector_valuation_explorer/`  
**UI:** sector directory + sector workspace inside Valuation Terminal

## Flow

```text
Market → Sector → Industry → Company → Historical Valuation → Research
```

Company search remains available. Analysts can also start from **All Sectors**.

## Data path

```text
Warehouse → Market Intelligence universe → sector_lens / VPAE
         → HVIE historical_sector_medians
         → Sector Valuation Explorer APIs
         → Valuation Terminal UI
```

No UI calculations. No BUY/SELL language.

## APIs

| Route | Purpose |
|---|---|
| `GET /v1/valuation/sectors` | Sector directory cards |
| `GET /v1/valuation/sector/{sector}` | Full sector workspace pack |
| `GET /v1/valuation/sector/{sector}/summary` | Dashboard + explanation + outcome |
| `GET /v1/valuation/sector/{sector}/companies` | Filterable company table |
| `GET /v1/valuation/sector/{sector}/leaders` | Top-10 leaderboards |
| `GET /v1/valuation/sector/{sector}/heatmap` | Percentile color cells |
| `GET /v1/valuation/sector/{sector}/research` | Research priorities |
| `GET /v1/valuation/company/{symbol}` | UVE terminal company pack |
| `GET /v1/valuation/company/{symbol}/history` | HVIE history |

Mirrored under `/api/intelligence/valuation/*`.

## Sections

1. Sector directory cards (median PE/PB, historical %, opportunity)
2. Sector dashboard
3. Sector explanation (`sector_lens` — not duplicated)
4. Sector outcome (analysis + confidence)
5. Company valuation table + filters + quick buttons
6. Compare 2–5 companies
7. Distributions (server-provided bins)
8. Leaders
9. Research priorities

## Acceptance

- Every primary sector listed below company search
- Sector click opens institutional workspace
- Company rows include valuation status from VPAE/HVIE context
- All values warehouse-backed through UVE / HVIE / VPAE
