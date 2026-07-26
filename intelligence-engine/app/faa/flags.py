"""FAA feature flags."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class FaaFlags:
    faa: bool = True
    faa_discovery: bool = True
    faa_fetch: bool = True
    faa_processing: bool = True
    faa_index: bool = True
    faa_live_fetch: bool = False  # offline-safe default; enable for live HTTP
    faa_search_api: bool = True
    faa_pdf: bool = True
    faa_notify_fre: bool = True
    faa_scheduler: bool = True

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "FaaFlags":
        s = settings or get_settings()
        return cls(
            faa=bool(getattr(s, "faa", True)),
            faa_discovery=bool(getattr(s, "faa_discovery", True)),
            faa_fetch=bool(getattr(s, "faa_fetch", True)),
            faa_processing=bool(getattr(s, "faa_processing", True)),
            faa_index=bool(getattr(s, "faa_index", True)),
            faa_live_fetch=bool(getattr(s, "faa_live_fetch", False)),
            faa_search_api=bool(getattr(s, "faa_search_api", True)),
            faa_pdf=bool(getattr(s, "faa_pdf", True)),
            faa_notify_fre=bool(getattr(s, "faa_notify_fre", True)),
            faa_scheduler=bool(getattr(s, "faa_scheduler", True)),
        )

    def as_dict(self) -> dict[str, bool]:
        return {
            "FAA": self.faa,
            "FAA_DISCOVERY": self.faa_discovery,
            "FAA_FETCH": self.faa_fetch,
            "FAA_PROCESSING": self.faa_processing,
            "FAA_INDEX": self.faa_index,
            "FAA_LIVE_FETCH": self.faa_live_fetch,
            "FAA_SEARCH_API": self.faa_search_api,
            "FAA_PDF": self.faa_pdf,
            "FAA_NOTIFY_FRE": self.faa_notify_fre,
            "FAA_SCHEDULER": self.faa_scheduler,
        }
