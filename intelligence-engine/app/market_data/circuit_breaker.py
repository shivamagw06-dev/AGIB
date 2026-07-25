"""Per-provider circuit breaker for failover."""

from __future__ import annotations

import threading
import time
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    def __init__(self, provider_id: str, retry_after_s: float) -> None:
        self.provider_id = provider_id
        self.retry_after_s = retry_after_s
        super().__init__(f"circuit open: {provider_id}; retry_after_s={retry_after_s:.3f}")


class CircuitBreaker:
    def __init__(
        self,
        provider_id: str,
        *,
        failure_threshold: int = 3,
        recovery_timeout_s: float = 30.0,
        half_open_successes: int = 1,
    ) -> None:
        self.provider_id = provider_id
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.half_open_successes = half_open_successes
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._half_open_ok = 0
        self._opened_at = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_half_open()
            return self._state

    def _maybe_half_open(self) -> None:
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self.recovery_timeout_s:
                self._state = CircuitState.HALF_OPEN
                self._half_open_ok = 0

    def before_call(self) -> None:
        with self._lock:
            self._maybe_half_open()
            if self._state == CircuitState.OPEN:
                retry_after = max(0.0, self.recovery_timeout_s - (time.monotonic() - self._opened_at))
                raise CircuitOpenError(self.provider_id, retry_after)

    def record_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_ok += 1
                if self._half_open_ok >= self.half_open_successes:
                    self._state = CircuitState.CLOSED
                    self._failures = 0
            else:
                self._failures = 0
                self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._state == CircuitState.HALF_OPEN or self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._half_open_ok = 0


class CircuitBreakerRegistry:
    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get(self, provider_id: str) -> CircuitBreaker:
        with self._lock:
            breaker = self._breakers.get(provider_id)
            if breaker is None:
                breaker = CircuitBreaker(provider_id)
                self._breakers[provider_id] = breaker
            return breaker

    def snapshot(self) -> dict[str, str]:
        with self._lock:
            return {pid: br.state.value for pid, br in self._breakers.items()}
