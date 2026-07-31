# Mission Control Snapshot Architecture (PR1)

## Goal

Opening Mission Control must **never** run `build_mission_control()` on the HTTP path.
The intelligence worker (or gather sidecar) builds a durable snapshot; HTTP only reads it.

## Layout

```text
$KIP_DATA_DIR/mission_control/
  snapshot.json      # Mission Control desk (PR1)
  agent_map.json     # Agent Map panel (PR2)
```

Atomic write: temp → fsync → rename (via `institutional_data.persistence.atomic`).

## Who builds

| Process | Builds snapshot? |
|---|---|
| `gather_worker.py` (sidecar or dedicated worker) | **Yes** — boot + every `MC_SNAPSHOT_INTERVAL_SEC` (default 600s) + after CGL |
| HTTP `AGI_ROLE=web` + `AGI_GATHER_SIDECAR=true` | **No** — sidecar shares disk and builds |
| HTTP `AGI_ROLE=web` + `AGI_GATHER_SIDECAR=false` | **Yes (background)** — dedicated worker has a separate Render disk |

## HTTP contract

| Method | Path | Behavior |
|---|---|---|
| GET | `/v1/mission-control/dashboard` | Read snapshot or `{status:warming}` — never compute |
| GET | `/v1/mission-control/agent-map` | Read `agent_map.json` or warming — never `build_agent_map()` |
| GET | `/v1/mission-control/health` | Flags + snapshot meta + job status |
| POST | `/v1/mission-control/rebuild` | Queue background rebuild (+ Agent Map refresh); return immediately |
| GET | `/v1/mission-control/report` | Slice of snapshot only |
| GET | `/v1/mission-control/quality-gates` | Snapshot only |

## Frontend

- On open: dashboard + health only
- Poll snapshot every **90s**, health every **45s**
- Warming UI when snapshot missing (no endless spinner)
- Never triggers live analytics rebuild

## Env

| Key | Default | Meaning |
|---|---|---|
| `MC_SNAPSHOT_INTERVAL_SEC` | `600` | Rebuild interval (min 60) |
| `MC_SNAPSHOT_ROOT` | `$KIP_DATA_DIR/mission_control` | Override store path |
| `AGI_MC_SNAPSHOT_BUILDER` | auto | Force on/off local web builder |
| `MC_ALLOW_LIVE_IN_PYTEST` | unset | Set `1` to run real aggregate in tests |

## Agent Map (PR2)

- Built in the same worker loop immediately after each Mission Control snapshot
- Also enqueued on boot if `agent_map.json` is missing
- Frontend panel polls every 90s **only while open**

## Follow-ups

- PR3 Intelligence Map cached probes
- PR4 Institutional Intelligence snapshot boards
- Optional section files (`coverage.json`, `fire.json`, …) if summary exceeds ~1MB
