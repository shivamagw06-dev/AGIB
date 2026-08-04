#!/usr/bin/env python3
"""AGI gather worker — CGL + FAA + FSE outside the HTTP / uvicorn process.

Run as:
  - Sidecar on the same Render web instance (shared disk, $0 extra), or
  - Dedicated Render Background Worker (agib-intelligence-worker).

The HTTP process must keep CONTINUOUS_GATHER_LEARN=false and
FAA_BACKGROUND_COLLECTOR=false so Ask / Mission Control stay responsive.
This process enables gather loops and owns the heavy ingest work.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

# Ensure intelligence-engine root is on sys.path when launched as a script.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _truthy(name: str, default: str = "false") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def _apply_worker_defaults() -> None:
    """Ensure gather flags are on for this process (sidecar overrides parent false)."""
    os.environ["AGI_ROLE"] = "gather_worker"
    defaults = {
        "CONTINUOUS_GATHER_LEARN": "true",
        "FAA_BACKGROUND_COLLECTOR": "true",
        "CONTINUOUS_HISTORICAL_BACKFILL": "true",
        "CONTINUOUS_BACKFILL_UNTIL_COMPLETE": "true",
        "KF_HD_LIVE_COLLECTORS": "true",
        "CONTINUOUS_FAA_REFRESH": "true",
        "CONTINUOUS_LIDI": "true",
        "CONTINUOUS_KF_HD": "true",
        "CONTINUOUS_LEARNING_LOOP": "true",
        "CONTINUOUS_MORNING_DAG": "true",
        "WAREHOUSE_DAILY_REFRESH": "true",
        "WAREHOUSE_BACKFILL": "true",
    }
    # Sidecar start script exports these true already; still fill gaps.
    for key, value in defaults.items():
        if not str(os.environ.get(key) or "").strip():
            os.environ[key] = value
    # When launched as dedicated worker OR with AGI_GATHER_FORCE=1, force on
    # even if Blueprint left false on a shared env block.
    if _truthy("AGI_GATHER_FORCE", "true"):
        for key, value in defaults.items():
            os.environ[key] = value


def main() -> int:
    _apply_worker_defaults()

    from app.core.logging import configure_logging, get_logger

    configure_logging()
    log = get_logger("agi.gather_worker")
    log.info(
        "gather_worker_starting",
        extra={
            "role": os.environ.get("AGI_ROLE"),
            "cgl": os.environ.get("CONTINUOUS_GATHER_LEARN"),
            "faa_bg": os.environ.get("FAA_BACKGROUND_COLLECTOR"),
            "kip_data_dir": os.environ.get("KIP_DATA_DIR"),
        },
    )

    stop_fns: list = []

    try:
        from continuous_gather_learn.production import start as start_cgl
        from continuous_gather_learn.production import stop as stop_cgl

        boot_cgl = start_cgl()
        stop_fns.append(stop_cgl)
        log.info("gather_worker_cgl", extra=boot_cgl if isinstance(boot_cgl, dict) else {"boot": boot_cgl})
    except Exception as exc:  # noqa: BLE001
        log.warning("gather_worker_cgl_failed", extra={"error": str(exc)[:200]})

    try:
        from app.faa.background import start_background_collector, stop_background_collector
        from app.faa.service import FaaService

        faa = FaaService(fre=None, aoi=None)
        boot_faa = start_background_collector(lambda: faa)
        stop_fns.append(stop_background_collector)
        log.info("gather_worker_faa", extra=boot_faa if isinstance(boot_faa, dict) else {"boot": boot_faa})
    except Exception as exc:  # noqa: BLE001
        log.warning("gather_worker_faa_failed", extra={"error": str(exc)[:200]})

    try:
        from financial_statements_engine.orchestrator.subscriber import bind_orchestrator_subscriber

        bind_orchestrator_subscriber()
        log.info("gather_worker_fse_bound", extra={"subscriber": "fse00_orchestrator"})
    except Exception as exc:  # noqa: BLE001
        log.warning("gather_worker_fse_bind_failed", extra={"error": str(exc)[:200]})

    # Mission Control snapshot builder — HTTP only reads; this process computes.
    try:
        from mission_control.snapshot import start_scheduler as start_mc_snapshot
        from mission_control.snapshot import stop_scheduler as stop_mc_snapshot

        boot_mc = start_mc_snapshot(boot_build=True)
        stop_fns.append(stop_mc_snapshot)
        log.info("gather_worker_mc_snapshot", extra=boot_mc if isinstance(boot_mc, dict) else {"boot": boot_mc})
    except Exception as exc:  # noqa: BLE001
        log.warning("gather_worker_mc_snapshot_failed", extra={"error": str(exc)[:200]})

    # Institutional Data Warehouse — daily refresh after the Indian close.
    try:
        from institutional_warehouse.scheduler import start as start_warehouse
        from institutional_warehouse.scheduler import stop as stop_warehouse

        boot_warehouse = start_warehouse()
        if boot_warehouse.get("enabled"):
            stop_fns.append(stop_warehouse)
        log.info("gather_worker_warehouse", extra=boot_warehouse)

        # Historical backfill runs here and nowhere else: a universe pass is
        # thousands of HTTP calls and must never sit in front of Ask.
        from institutional_warehouse.scheduler import start_backfill, stop_backfill

        boot_backfill = start_backfill()
        if boot_backfill.get("enabled"):
            stop_fns.append(stop_backfill)
        log.info("gather_worker_warehouse_backfill", extra=boot_backfill)
    except Exception as exc:  # noqa: BLE001
        log.warning("gather_worker_warehouse_failed", extra={"error": str(exc)[:200]})

    stopping = {"flag": False}

    def _handle_stop(signum, _frame):  # noqa: ANN001
        stopping["flag"] = True
        log.info("gather_worker_signal", extra={"signum": int(signum)})

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    log.info("gather_worker_ready")
    while not stopping["flag"]:
        time.sleep(5.0)

    for fn in stop_fns:
        try:
            fn()
        except Exception:
            pass
    log.info("gather_worker_stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
