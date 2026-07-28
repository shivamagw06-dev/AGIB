"""Change detection — material deltas become Learning Events (AGI's learning signal)."""

from __future__ import annotations

from typing import Any

from app.config.settings import Settings
from app.contracts.models import KnowledgeObject, KnowledgeObjectType, LearningEvent
from app.storage.db import KaipStore


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class ChangeDetector:
    def __init__(self, store: KaipStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings

    def detect(self, ko: KnowledgeObject, previous: KnowledgeObject | None) -> list[LearningEvent]:
        if previous is None:
            # First observation of corporate action / event is material by default
            if ko.object_type in {
                KnowledgeObjectType.CORPORATE_ACTION,
                KnowledgeObjectType.CORPORATE_EVENT,
            }:
                return [
                    LearningEvent(
                        company_symbol=ko.company_symbol,
                        field_name="object_created",
                        previous_value=None,
                        new_value=ko.object_type.value,
                        delta=1,
                        reason=f"New {ko.object_type.value} observed",
                        object_type=ko.object_type,
                        object_id=ko.object_id,
                        source_event_ids=list(ko.source_event_ids),
                    )
                ]
            return []

        events: list[LearningEvent] = []
        prev = previous.payload
        cur = ko.payload

        if ko.object_type == KnowledgeObjectType.MARKET_SNAPSHOT:
            events.extend(self._market_changes(ko, prev, cur))
        elif ko.object_type == KnowledgeObjectType.FINANCIAL_STATEMENT:
            events.extend(self._financial_changes(ko, prev, cur))
        elif ko.object_type == KnowledgeObjectType.COMPANY_PROFILE:
            for field in ("sector", "industry", "company_name"):
                if prev.get(field) and cur.get(field) and prev.get(field) != cur.get(field):
                    events.append(
                        LearningEvent(
                            company_symbol=ko.company_symbol,
                            field_name=field,
                            previous_value=prev.get(field),
                            new_value=cur.get(field),
                            reason=f"{field} changed",
                            object_type=ko.object_type,
                            object_id=ko.object_id,
                            source_event_ids=list(ko.source_event_ids),
                        )
                    )
        elif ko.object_type == KnowledgeObjectType.CORPORATE_ACTION:
            if prev.get("action_type") != cur.get("action_type") or prev.get("ex_date") != cur.get("ex_date"):
                events.append(
                    LearningEvent(
                        company_symbol=ko.company_symbol,
                        field_name="corporate_action",
                        previous_value=prev.get("action_type"),
                        new_value=cur.get("action_type"),
                        reason="Corporate action changed",
                        object_type=ko.object_type,
                        object_id=ko.object_id,
                        source_event_ids=list(ko.source_event_ids),
                    )
                )
        return events

    def _market_changes(
        self, ko: KnowledgeObject, prev: dict[str, Any], cur: dict[str, Any]
    ) -> list[LearningEvent]:
        out: list[LearningEvent] = []
        prev_pe = _num(prev.get("pe_ratio"))
        cur_pe = _num(cur.get("pe_ratio"))
        if prev_pe is not None and cur_pe is not None:
            delta = abs(cur_pe - prev_pe)
            # PE 24.1 → 24.2 ignored; only material absolute moves
            if delta >= self.settings.pe_material_abs:
                out.append(
                    LearningEvent(
                        company_symbol=ko.company_symbol,
                        field_name="pe_ratio",
                        previous_value=prev_pe,
                        new_value=cur_pe,
                        delta=round(cur_pe - prev_pe, 6),
                        reason=f"PE moved by {delta:.2f}",
                        object_type=ko.object_type,
                        object_id=ko.object_id,
                        source_event_ids=list(ko.source_event_ids),
                    )
                )

        prev_px = _num(prev.get("last_price"))
        cur_px = _num(cur.get("last_price"))
        if prev_px and cur_px and prev_px != 0:
            pct = abs((cur_px - prev_px) / prev_px) * 100.0
            if pct >= self.settings.price_material_pct:
                out.append(
                    LearningEvent(
                        company_symbol=ko.company_symbol,
                        field_name="last_price",
                        previous_value=prev_px,
                        new_value=cur_px,
                        delta=round(pct, 4),
                        reason=f"Price moved {pct:.2f}%",
                        object_type=ko.object_type,
                        object_id=ko.object_id,
                        source_event_ids=list(ko.source_event_ids),
                    )
                )
        return out

    def _financial_changes(
        self, ko: KnowledgeObject, prev: dict[str, Any], cur: dict[str, Any]
    ) -> list[LearningEvent]:
        out: list[LearningEvent] = []
        # Support both ratio (0.18) and percent (18)
        def as_pct(v: float | None) -> float | None:
            if v is None:
                return None
            return v * 100.0 if abs(v) <= 1.5 else v

        prev_g = as_pct(_num(prev.get("revenue_growth")))
        cur_g = as_pct(_num(cur.get("revenue_growth")))
        if prev_g is not None and cur_g is not None:
            delta_pp = abs(cur_g - prev_g)
            if delta_pp >= self.settings.revenue_growth_material_pp:
                out.append(
                    LearningEvent(
                        company_symbol=ko.company_symbol,
                        field_name="revenue_growth",
                        previous_value=prev_g,
                        new_value=cur_g,
                        delta=round(cur_g - prev_g, 4),
                        reason=f"Revenue growth moved {delta_pp:.1f} percentage points",
                        object_type=ko.object_type,
                        object_id=ko.object_id,
                        source_event_ids=list(ko.source_event_ids),
                    )
                )
        return out
