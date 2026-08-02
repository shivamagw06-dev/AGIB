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
