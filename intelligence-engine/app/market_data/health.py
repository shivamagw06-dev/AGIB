"""Provider health service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.market_data.circuit_breaker import CircuitBreakerRegistry
from app.market_data.metrics import MarketDataMetrics
from app.market_data.registry import ProviderRegistry


@dataclass
class ProviderHealth:
    provider_id: str
    configured: bool
    circuit_state: str
    capabilities: list[str] = field(default_factory=list)
    last_error: str | None = None
    ok: bool = True


class ProviderHealthService:
    def __init__(
        self,
        registry: ProviderRegistry,
        circuits: CircuitBreakerRegistry,
        metrics: MarketDataMetrics,
    ) -> None:
        self.registry = registry
        self.circuits = circuits
        self.metrics = metrics
        self._last_errors: dict[str, str] = {}

    def record_error(self, provider_id: str, message: str) -> None:
        self._last_errors[provider_id] = message

    def snapshot(self) -> dict[str, object]:
        circuit_states = self.circuits.snapshot()
        providers: list[dict[str, object]] = []
        for provider in self.registry.list_providers():
            state = circuit_states.get(provider.provider_id, "closed")
            configured = provider.is_configured()
            ok = configured and state != "open"
            row: dict[str, object] = {
                "provider_id": provider.provider_id,
                "configured": configured,
                "circuit_state": state,
                "capabilities": sorted(provider.capabilities()),
                "priority": provider.priority,
                "last_error": self._last_errors.get(provider.provider_id),
                "ok": ok,
            }
            # Soft extras (Yahoo health dashboard fields)
            if hasattr(provider, "health_extras"):
                try:
                    row["extras"] = provider.health_extras()  # type: ignore[operator]
                except Exception:
                    pass
            providers.append(row)
        return {
            "ok": any(p["ok"] for p in providers) if providers else False,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "providers": providers,
            "metrics": self.metrics.snapshot(),
        }
