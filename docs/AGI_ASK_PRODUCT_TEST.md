# AGI Ask Product Test Suite (Founder Acceptance)

## What it is

Product-level validation for AGI Ask — not routing-only, PAT stubs, or UI file smoke.

```bash
Browser/API → POST /api/ui/search → UiService.search → Response pack
```

## Files

| Path | Role |
|------|------|
| `intelligence-engine/ask_product_test/` | Harness, checks, fixtures, prompts |
| `intelligence-engine/tests/test_ask_product_smoke.py` | Tier A (8 prompts) |
| `intelligence-engine/tests/test_ask_product_regression.py` | Tier B (CIO-25 + isolation + determinism) |
| `artifacts/ask_test_report.json` | Per-question metrics after each run |

## Modes

| `ASK_TEST_MODE` | Behavior |
|-----------------|----------|
| `contract` (default) | Deterministic SearchView fixtures — CI-safe product-contract gate |
| `inprocess` | Real `UiService.search` (slow; local engine) |
| `live` | `POST {ASK_TEST_BASE}/api/ui/search` — founder live gate |

## Commands

```bash
cd intelligence-engine

# CI / default — contract mode
pytest tests/test_ask_product_smoke.py tests/test_ask_product_regression.py -q

# Founder live acceptance against Render gateway
ASK_TEST_MODE=live \
ASK_TEST_BASE=https://finance-news-backend-19i5.onrender.com \
  pytest tests/test_ask_product_smoke.py tests/test_ask_product_regression.py -q

# Sample regression
ASK_TEST_REGRESSION_LIMIT=5 pytest tests/test_ask_product_regression.py -q
```

## Gates

- Tier A: **100%** pass
- Tier B: **≥ 95%** pass
- No recommendation-policy violations
- No HTML/502-shaped crashes (structured degraded JSON allowed)
- Report artifact written every run
