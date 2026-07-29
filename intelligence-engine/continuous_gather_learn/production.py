"""Continuous Gather → Learn production facade."""

from __future__ import annotations

from typing import Any

from continuous_gather_learn import persist as cgl_persist
from continuous_gather_learn.background import last_status, start_background_loop, stop_background_loop
from continuous_gather_learn.flags import flags_dict, is_enabled
from continuous_gather_learn.orchestrator import learning_for_director, run_cycle, select_slot

PROGRAMME = "AGIB Continuous Gather → Learn"
VERSION = "cgl-v1.0.0"


def health() -> dict[str, Any]:
    return {
        "status": "ok" if is_enabled() else "disabled",
        "programme": PROGRAMME,
        "version": VERSION,
        "enabled": is_enabled(),
        "ask_isolated": True,
        "ml_retrain": False,
        "learning_mode": "structured_knowledge_and_forecast_calibration",
        "store_root": str(cgl_persist.store_root()),
        "flags": flags_dict(),
        "background": last_status(),
        "components": [
            "LIDI",
            "Knowledge Factory Historical Depth",
            "FAA Background / CGL FAA refresh",
            "Institutional Scheduler morning DAG",
            "FVL",
            "FLE",
            "ILO",
            "CAL",
            "ResearchDirector learning inject",
        ],
    }


def dashboard() -> dict[str, Any]:
    metrics = cgl_persist.get_metrics()
    latest = cgl_persist.get_latest_run()
    return {
        "enabled": is_enabled(),
        "programme": PROGRAMME,
        "version": VERSION,
        "current_slot": select_slot(),
        "metrics": metrics,
        "latest_run": {
            "run_id": latest.get("run_id"),
            "ok": latest.get("ok"),
            "slot": latest.get("slot"),
            "latency_ms": latest.get("latency_ms"),
            "volumes": latest.get("volumes"),
            "generated_at": latest.get("generated_at"),
            "errors": (latest.get("errors") or [])[:5],
        },
        "checkpoints": {
            "lidi": cgl_persist.get_checkpoint("lidi"),
            "kf_hd": cgl_persist.get_checkpoint("kf_hd"),
            "analyst_accuracy_memory": cgl_persist.get_checkpoint("analyst_accuracy_memory"),
        },
        "background": last_status(),
        "knowledge_growth": metrics.get("knowledge_growth") or {},
        "freshness": (metrics.get("freshness") or {}),
        "archived_learnings": len(cgl_persist.list_archived_learnings(limit=2000)),
        "flags": flags_dict(),
        "loop": [
            "Collect",
            "Validate",
            "Clean",
            "Store",
            "Embed/Extract",
            "Update knowledge",
            "Generate signals",
            "Evaluate forecasts",
            "Learn",
            "Update confidence",
            "Archive",
        ],
        "north_star": "Continuously gather historical data and improve institutional knowledge without user interaction.",
    }


def run(**kwargs: Any) -> dict[str, Any]:
    return run_cycle(**kwargs)


def director_learning(*, query: str = "", limit: int = 8) -> dict[str, Any]:
    return learning_for_director(query=query, limit=limit)


def start() -> dict[str, Any]:
    return start_background_loop()


def stop() -> dict[str, Any]:
    return stop_background_loop()
