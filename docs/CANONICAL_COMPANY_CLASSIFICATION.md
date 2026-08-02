# Canonical Company Classification (Company Identity Service)

**Priority:** P0 — production blocker
**Rule:** Capital IQ is the single source of truth for company identity and
classification. No engine may infer a company's sector, industry, business
type, valuation framework, KPIs, or business model when the company exists in
the Capital IQ master.

## The bug this eliminates

Asking for **Axis Bank** returned:

```
Business Type:            Conglomerate
Enterprise Value Drivers: GRM, Production, Reserve Replacement, Refining Complexity
Industry DNA:             Banks
```

Root cause chain:

1. Capital IQ classifies Axis Bank as **Diversified Banks**.
2. Business Intelligence keyword-matched the label and hit its `diversified`
   alias before its `bank` alias, producing `conglomerate`.
3. `conglomerate` was mapped to `oil_gas` as a "soft fallback", so a bank was
   handed refining value drivers.

All three links are now removed. Classification comes from a canonical service
keyed on the Capital IQ **Primary Industry** — never from a description.

## Company Identity Service

`intelligence-engine/company_identity/`

```json
{
  "ticker": "AXISBANK",
  "company_name": "Axis Bank Limited",
  "primary_sector": "Financials",
  "primary_industry": "Diversified Banks",
  "business_type": "Universal Bank",
  "industry_dna": "banks"
}
```

| Module | Responsibility |
|---|---|
| `service.py` | Resolve identity by ticker, exact name, or company mention |
| `taxonomy.py` | Primary Industry → archetype / DNA / valuation framework / KPIs |
| `guard.py` | Cross-industry leakage and wrong-classification detection |
| `schema.py` | Immutable `CompanyIdentity` contract and the 11 primary sectors |

Resolution order: `valuation_consensus` (CapIQ Broker Estimates master) →
`institutional_knowledge_tables` (CapIQ screener exports). Coverage is **100%
of 2,987 companies**, with zero unmapped industries.

### Primary sectors

Only these eleven labels are ever emitted: Communication Services, Consumer
Discretionary, Consumer Staples, Energy, Financials, Health Care, Industrials,
Information Technology, Materials, Real Estate, Utilities.

### Mention resolution

A company binds only when it is unambiguous. Longest canonical name in the
question wins, then a unique prefix, then a single distinctive token.

| Mention | Binds |
|---|---|
| `Oil and Natural Gas Corporation Limited's business model?` | `ONGC` |
| `Indian Oil Corporation Limited` | `IOC` |
| `Apollo Hospitals` | `APOLLOHOSP` (not Apollo Micro Systems) |
| `Apollo`, `HDFC`, `Tata` | refused — ambiguous |
| `Air India` | refused — not in the listed universe |

## Precedence

```
Capital IQ Master → Industry DNA → Business Intelligence → Investment
→ Research → Market → Historical → Forecast
```

Fusion may enrich but never overwrite. Any fused line carrying another
industry's exclusive vocabulary is dropped, and a contaminated summary is
replaced. Every answer carries `diagnostics.company_identity` and
`diagnostics.classification_guard`.

## Automatic fails

Financials + GRM · Banks + Production · IT + Reserve Replacement ·
Hospitals + CASA · Retail + NIM · Airline + Oil Production ·
Conglomerate returned for Axis Bank · wrong Primary Sector · wrong Primary Industry.

Terms shared legitimately between allied families are not leaks — FMCG may use
SSSG, and a power producer may use plant load factor.

## API

| Route | Purpose |
|---|---|
| `GET /v1/company-identity/health` | Coverage and classification rate |
| `GET /v1/company-identity/{ticker}` | Full canonical identity |
| `POST /v1/company-identity/validate` | Check text or a classification claim |

Node BFF mirrors these under `/api/intelligence/company-identity/*`.

## Release gate

`ask_product_test/run_canonical_classification_acceptance_v1.py` — 300
questions across all 11 sectors, verifying Primary Sector, Primary Industry,
Business Type, Industry DNA, Valuation Framework, KPI Dictionary and Business
Model consistency, including the 30 golden companies.

Current result: **300/300 (100%)**, golden **150/150**, sectors **11/11**,
cross-industry leakage **0**, wrong sector **0**, wrong industry **0**.

Unit contract: `company_identity/tests/test_company_identity.py`.
