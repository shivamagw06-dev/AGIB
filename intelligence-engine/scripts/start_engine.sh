#!/usr/bin/env bash
# Start HTTP (uvicorn) + gather sidecar as separate processes on one instance.
#
# Why: FSE/CGL/FAA in the uvicorn process starve Ask / Mission Control.
# Separate OS processes share the Render disk but not the asyncio event loop.
#
# Set AGI_GATHER_SIDECAR=false to run HTTP only (use dedicated worker instead).
set -euo pipefail

cd "$(dirname "$0")/.."

GATHER_PID=""

cleanup() {
  if [[ -n "${GATHER_PID}" ]] && kill -0 "${GATHER_PID}" 2>/dev/null; then
    kill -TERM "${GATHER_PID}" 2>/dev/null || true
    wait "${GATHER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ "${AGI_GATHER_SIDECAR:-true}" != "false" && "${AGI_GATHER_SIDECAR:-true}" != "0" ]]; then
  echo "[start_engine] launching gather sidecar (CGL/FAA/FSE)"
  (
    export AGI_ROLE=gather_worker
    export AGI_GATHER_FORCE=true
    export CONTINUOUS_GATHER_LEARN=true
    export FAA_BACKGROUND_COLLECTOR=true
    export CONTINUOUS_HISTORICAL_BACKFILL=true
    export CONTINUOUS_BACKFILL_UNTIL_COMPLETE=true
    export KF_HD_LIVE_COLLECTORS=true
    export CONTINUOUS_FAA_REFRESH=true
    export CONTINUOUS_LIDI=true
    export CONTINUOUS_KF_HD=true
    export CONTINUOUS_LEARNING_LOOP=true
    export CONTINUOUS_MORNING_DAG=true
    exec python scripts/gather_worker.py
  ) &
  GATHER_PID=$!
  echo "[start_engine] gather sidecar pid=${GATHER_PID}"
else
  echo "[start_engine] AGI_GATHER_SIDECAR=false — HTTP only (use agib-intelligence-worker)"
fi

# HTTP process: never run in-process gather loops.
export AGI_ROLE=web
export CONTINUOUS_GATHER_LEARN=false
export FAA_BACKGROUND_COLLECTOR=false
export CONTINUOUS_HISTORICAL_BACKFILL=false
# Keep KF live collectors off in HTTP; sidecar/worker owns backfill.
export KF_HD_LIVE_COLLECTORS=false

echo "[start_engine] launching uvicorn on port ${PORT:-8100}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8100}"
