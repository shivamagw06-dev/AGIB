# AGI Valuation Intelligence Terminal

**Route:** `/valuation-terminal` (public) · `/admin/valuation-terminal` (admin)
**Engine:** `intelligence-engine/valuation_terminal/`

Not a screener. An institutional valuation workspace that answers four
questions for every company: how is it valued today, how does that compare
with peers, why is the market assigning that valuation, and what would change
it.

## Two layers, never mixed

| Layer | Source |
|---|---|
| Market data | Yahoo Finance multiples · Capital IQ consensus, reported as published |
| Interpretation | AGI — which metric governs, peer position, what drives a re-rating |

No BUY/SELL, no AGI price targets.

## Sector-aware metrics

Metric visibility is driven by canonical Industry DNA, not by whatever the
vendor returned. A bank has no meaningful EV/EBITDA, so the terminal shows
`n/a` with the reason rather than a misleading number.

| Industry | Primary | Suppressed |
|---|---|---|
| Banks, NBFC, insurance | P/B | EV/EBITDA, EV/Sales, P/S |
| Energy, metals, cement, utilities | EV/EBITDA | — |
| IT services, FMCG, pharma, autos | P/E | P/B (IT) |
| Software, internet platforms | EV/Sales | P/B |
| Real estate | P/B | EV/EBITDA |
| Airlines | EV/EBITDA | P/B, P/E |

## Sections

1. **Market dashboard** — companies covered, median P/E, P/B, EV/EBITDA
   (excluding financials), ROE, dividend yield, cheapest and most expensive
   sector.
2. **Sector cards** — one per Capital IQ primary sector with medians and the
   metric that governs it.
3. **AGI Sector Intelligence** — industry DNA, primary and supporting metrics,
   metrics to avoid, the current market picture, interpretation written from
   that sector's own numbers, and what drives a re-rating.
4. **Company table** — sortable, sector-aware columns; suppressed metrics show
   as `n/a` with a tooltip.
5. **Company expansion** — market metrics, Capital IQ consensus, AGI valuation
   view, and a peer comparison against the same industry on its governing
   metric.
6. **Institutional insights** — generated from the data, refreshed on ingest.
7. **Metric explainers** — what each metric is, why it matters, where it
   applies and how to read it.

## Data

`market_data/nse_valuation.json` — **1,184 NSE companies**, 14 metrics each,
pulled from Yahoo Finance and joined to Company Identity (1,175 resolved).

Field coverage on the Nifty 500 subset: EPS and margins 100%, P/B and book
value 99%, market cap and EV/Revenue 97%, forward P/E 96%, trailing P/E 95%,
debt/equity 92%, dividend yield and EV/EBITDA 84%, ROE 50%.

Yahoo rate-limits bulk pulls: 1,184 of 2,364 NSE listings resolved in one
pass. The remainder needs a slower scheduled backfill.

## API

| Route | Purpose |
|---|---|
| `GET /v1/valuation-terminal/health` | Coverage and field completeness |
| `GET /v1/valuation-terminal/overview` | Market dashboard |
| `GET /v1/valuation-terminal/sectors` | Sector cards |
| `GET /v1/valuation-terminal/sector/{sector}` | AGI sector intelligence |
| `GET /v1/valuation-terminal/companies` | Table with filters and sorting |
| `GET /v1/valuation-terminal/company/{ticker}` | Company detail with peers |
| `GET /v1/valuation-terminal/insights` | Generated insights |
| `GET /v1/valuation-terminal/explain/{metric}` | Metric pedagogy |
| `POST /v1/valuation-terminal/ingest` | Load committed market-data pulls |

Mirrored on the Node BFF under `/api/intelligence/valuation-terminal/*`.

## Not yet built

Historical multiple charts (5/10-year P/E, P/B, EV/EBITDA bands) and
consensus target history. Both need a time series the current pull does not
carry.

## v2.0 — Backend calculation engine, percentiles and audited overrides

### No formulas in the UI

Every derived number is computed server-side in `valuation_terminal/calc.py`
from stored raw values, so the same figure is identical for every consumer and
traceable to its inputs:

| Derived | Formula |
|---|---|
| Upside % | (target − CMP) ÷ CMP, against the **latest** price rather than the vendor's older close |
| Premium vs sector | (value ÷ industry median) − 1 |
| Consensus spread | (high − low) ÷ mean target |
| Sector percentile | position within the industry population, 0 = cheapest |
| ROE premium | ROE against the industry median |

### Relative Valuation Score

A descriptive 0–100 position from sector percentile (45%), consensus (15%),
profitability against the sector (10%) and, once available, historical
percentile (30%). Bands: Deep Discount · Discount · Fair · Premium · Rich.

Never advice — it says where the market has placed the company, not what to do.

Worked examples from the loaded data:

| Company | Metric | Value | Industry median | Premium | Percentile | Score |
|---|---|---|---|---|---|---|
| Axis Bank | P/B | 1.71 | 1.40 | +22.1% | 67.9 | 60.7 Premium |
| Infosys | P/E | 14.58 | 23.42 | −37.8% | 21.2 | 40.0 Fair |
| NTPC | EV/EBITDA | 7.61 | 10.67 | −28.7% | 0.0 | 12.6 Deep Discount |

### Manual overrides with audit

Imported values are never overwritten. An override is a layer on top carrying
value, imported value, actor, reason, timestamp and version, with full history
per field and a global audit log. A reason is mandatory. Company responses
expose `field_provenance` so any number is attributable to a vendor or a named
person.

Fourteen fields are editable; derived metrics recalculate from the override
automatically.

### Statistics

`sector_statistics()` recomputes medians for 11 sectors and 136 industries from
raw values on every call, so percentiles and premiums never drift from the
underlying data.

### API additions

| Route | Purpose |
|---|---|
| `GET /v1/valuation-terminal/statistics` | Sector and industry medians |
| `GET /v1/valuation-terminal/overrides/audit` | Audit log and summary |
| `POST /v1/valuation-terminal/overrides` | Set an override (reason required) |
| `POST /v1/valuation-terminal/overrides/clear` | Revert to the imported value |

### Still outstanding from the v2.0 spec

- **Historical valuation** — current vs 5Y/10Y median, percentile and
  premium/discount per multiple. This is the spec's highest priority and is not
  built: it needs a fundamentals time series (historical EPS and book value per
  share) that the current pull does not carry. Price history alone would give a
  misleading "P/E band".
- **Groww daily price layer** and the 18:45 IST refresh pipeline.
- Sector heatmap, daily valuation intelligence digest, and the admin editable
  grid UI — the override engine and audit trail behind them are complete.
