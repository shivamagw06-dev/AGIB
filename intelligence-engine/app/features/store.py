"""In-memory historical / PIT feature store (FEAT-001 store layer)."""

from __future__ import annotations

import threading
from datetime import date, datetime

from app.features.models import FeatureMetadata, FeatureValue, HistoricalFeatureSeries


def _as_of_key(as_of: date | datetime | str) -> str:
    if isinstance(as_of, datetime):
        return as_of.date().isoformat()
    if isinstance(as_of, date):
        return as_of.isoformat()
    return str(as_of)[:10]


class FeatureStore:
    """PIT store: (feature_id, symbol, as_of) -> FeatureValue with available_at."""

    def __init__(self) -> None:
        self._meta: dict[str, FeatureMetadata] = {}
        self._values: dict[tuple[str, str, str], FeatureValue] = {}
        self._lock = threading.Lock()

    def upsert_metadata(self, meta: FeatureMetadata) -> None:
        with self._lock:
            self._meta[meta.feature_id] = meta

    def get_metadata(self, feature_id: str) -> FeatureMetadata | None:
        with self._lock:
            return self._meta.get(feature_id)

    def list_metadata(self) -> list[FeatureMetadata]:
        with self._lock:
            return sorted(self._meta.values(), key=lambda m: m.feature_id)

    def put_value(self, value: FeatureValue) -> None:
        symbol = value.symbol or ""
        key = (value.feature_id, symbol, _as_of_key(value.as_of))
        with self._lock:
            self._values[key] = value

    def get_value(
        self,
        feature_id: str,
        *,
        symbol: str | None,
        as_of: date | datetime | str,
        pit_mode: bool = True,
    ) -> FeatureValue | None:
        """Return value as-of. In pit_mode, require available_at date <= as_of."""
        symbol_key = symbol or ""
        as_of_s = _as_of_key(as_of)
        with self._lock:
            value = self._values.get((feature_id, symbol_key, as_of_s))
            if value is None:
                return None
            if pit_mode:
                available = value.available_at
                if isinstance(available, datetime):
                    available_day = available.date().isoformat()
                else:
                    available_day = str(available)[:10]
                if available_day > as_of_s:
                    return None
            return value

    def history(
        self,
        feature_id: str,
        *,
        symbol: str | None = None,
        formula_version: str | None = None,
    ) -> HistoricalFeatureSeries:
        symbol_key = symbol or ""
        with self._lock:
            points = [
                v
                for (fid, sym, _), v in self._values.items()
                if fid == feature_id and sym == symbol_key
                and (formula_version is None or v.formula_version == formula_version)
            ]
        points.sort(key=lambda p: _as_of_key(p.as_of))
        version = formula_version or (points[-1].formula_version if points else "")
        return HistoricalFeatureSeries(
            feature_id=feature_id,
            formula_version=version,
            symbol=symbol,
            points=points,
        )
