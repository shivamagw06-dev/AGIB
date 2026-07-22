# AGI Market Intelligence Engine

Architecture for compliant public display of market insights.

## Legal principle

| Category | Public display |
|----------|----------------|
| Raw exchange data (LTP, quotes, depth) | Only if license permits — **not shown on AGI public site** |
| AGI derived analytics | Yes — proprietary calculations |
| Editorial content | Yes — research, commentary |

## Data flow

```
Groww API (backend only)
        ↓
Calculation Engine (deterministic math)
  EMA · RSI · MACD · ADX · ATR · Breadth · Sector rank
        ↓
AGI Market Score (0–100)
        ↓
Summary Generator (explains results — optional GPT)
        ↓
Website (insights only)
```

## API endpoints

| Endpoint | Returns |
|----------|---------|
| `GET /api/market/intelligence` | Full AGI bundle (pulse, strip, sectors, stocks, summary) |
| `GET /api/market/dashboard` | Dashboard shape for frontend |
| `GET /api/market/ticker` | Insight strip (no raw prices) |

## Environment

```bash
GROWW_ACCESS_TOKEN=...   # or GROWW_API_KEY + GROWW_API_SECRET
```

## Update schedule

Engine recalculates every 5 minutes (configurable via `TTL` in `intelligenceService.js`).

## Before launch

Confirm with Groww support whether your subscription permits public redistribution of live quotes.
AGI displays **derived analytics only** regardless.
