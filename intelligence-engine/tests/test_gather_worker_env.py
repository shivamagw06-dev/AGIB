"""Gather worker env defaults — HTTP stays gather-off; worker forces gather-on."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def _load_gather_worker():
    path = Path(__file__).resolve().parents[1] / "scripts" / "gather_worker.py"
    spec = importlib.util.spec_from_file_location("gather_worker_mod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_gather_worker_force_enables_flags(monkeypatch):
    monkeypatch.setenv("AGI_GATHER_FORCE", "true")
    monkeypatch.setenv("CONTINUOUS_GATHER_LEARN", "false")
    monkeypatch.setenv("FAA_BACKGROUND_COLLECTOR", "false")
    monkeypatch.setenv("KF_HD_LIVE_COLLECTORS", "false")

    gw = _load_gather_worker()
    gw._apply_worker_defaults()

    assert os.environ["CONTINUOUS_GATHER_LEARN"] == "true"
    assert os.environ["FAA_BACKGROUND_COLLECTOR"] == "true"
    assert os.environ["KF_HD_LIVE_COLLECTORS"] == "true"
    assert os.environ["AGI_ROLE"] == "gather_worker"


def test_start_engine_script_exists():
    script = Path(__file__).resolve().parents[1] / "scripts" / "start_engine.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "gather_worker.py" in text
    assert "CONTINUOUS_GATHER_LEARN=false" in text
    assert "uvicorn app.main:app" in text
