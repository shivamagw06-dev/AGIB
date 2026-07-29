# Continuous Historical Backfill Until 100% Coverage

The historical backfill engine **does not stop after a fixed number of cycles**. It keeps draining a persistent company queue until every supported listed company is fully backfilled, then automatically switches to **maintenance-only** mode.

## Modes

| Mode | When | Behaviour |
|------|------|-----------|
| `deep_backfill` | `remaining > 0` | Prioritised batches every CGL slot; faster loop interval (default 300s) |
| `maintenance` | `remaining = 0` | Incremental refresh only; no full-history redownload; deep backfill disabled |

## Completion criteria

A company is **Fully Backfilled** only when hard dimensions pass (and soft dimensions are complete or transparently N/A after attempt):

- OHLCV depth ≥ target years (or listing age if newer)
- Corporate actions attempted / stored
- Annual + quarterly financials
- Knowledge extract + embeddings
- QA on prices
- Soft: announcements, AR / presentations / transcripts, shareholding, macro link

## Queue

Persistent under KF HD reports (`historical_backfill_queue`):

`company · priority · status · attempts · last_run · coverage · years · errors`

Priority: Nifty 50 → Next 50 → Nifty 500 → residual. Lowest coverage first. Failed names use exponential backoff.

## Flags

| Flag | Default | Meaning |
|------|---------|---------|
| `CONTINUOUS_HISTORICAL_BACKFILL` | true | Master backfill switch |
| `CONTINUOUS_BACKFILL_UNTIL_COMPLETE` | true | Keep draining until backlog=0 |
| `CONTINUOUS_BACKFILL_ACTIVE_INTERVAL_SEC` | 300 | CGL interval while backlog remains |
| `KF_HD_BACKFILL_BATCH` | 12 | Companies per batch |
| `KF_HD_BACKFILL_BATCHES_PER_CYCLE` | 3 | Batches per CGL wake |
| `KF_HD_BACKFILL_WORKERS` | 2 | Parallel workers |
| `KF_HD_TARGET_YEARS` | 15 | Depth target |
| `KF_HD_LIVE_COLLECTORS` | true (Render) | Yahoo live OHLCV |

## Mission Control

Shows total / fully backfilled / remaining / queue length / avg years / coverage % / ETA / processed today / extracts / embeddings / documents / backfill mode.
