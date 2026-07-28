# Sprint 6.5 — Adaptive Knowledge Orchestrator (AKO)

## Mission

Make the Knowledge Platform an **event-driven institutional learning system**.

AKO is the operating system of continuous knowledge acquisition: it schedules, prioritises, monitors and coordinates collectors — it does **not** collect, parse, or reason.

```text
AGI should continuously learn from the market,
not continuously research for the user.
```

## Contract

`knowledge-platform/docs/AKO_PLATFORM_CONTRACT.md`

## What shipped

- Market Clock + Session State (`PRE_MARKET` … `HOLIDAY`)
- Schedule Engine (session + event + load adaptive intervals)
- Priority Engine (institutional-critical jobs first)
- Event Engine + seed calendar (earnings, RBI policy)
- Collector Dispatcher (retry, backoff, dead-letter)
- Overnight rebuild hooks (published-knowledge only)
- Telemetry hub (every decision + execution observable)
- Mission Control soft APIs under `/v1/ako/*`
- Primary orchestrator via `KAIP_AKO=true` (default); fixed scheduler fallback

## Ask separation

```text
User Question → KRIG → Knowledge Store → Judgment → Answer
```

Ask / IE never call collectors. Ops-only `/v1/internal/run/{id}` remains Mission Control.

## Success path

```text
Infosys Earnings Today
  → AKO boosts Yahoo / NSE / Company IR polling
  → KAIP publishes updated Company Knowledge
  → Overnight rebuild refreshes learning / health
  → Ask retrieves via KRIG (no live collect)
```

## Verification

```bash
cd knowledge-platform && pytest -q
```

## Env

| Variable | Default | Meaning |
|---|---|---|
| `KAIP_AKO` | `true` | Use Adaptive Knowledge Orchestrator |
| `KAIP_AKO_TICK_SECONDS` | `1` | Evaluation loop cadence |
| `KAIP_SCHEDULER` | `true` | Start background orchestration |
| `KAIP_LIVE_COLLECTORS` | `true` | Allow external HTTP in collectors |

## Next

Sprint 6.6 — Knowledge Operations polish / Mission Control UI depth (optional), or Phase 7 reasoning integration against continuously refreshed knowledge.
