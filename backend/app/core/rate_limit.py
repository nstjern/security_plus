"""In-process sliding-window rate limiting.

Scope is one worker process: two Uvicorn workers each keep their own counters, so the real
limit is the configured value times the worker count. That is acceptable for slowing credential
stuffing against a personal study application, and inadequate for anything larger. Moving the
counters into Postgres or Redis is the upgrade path when it matters.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


class SlidingWindowRateLimiter:
    def __init__(self, *, max_attempts: int, window_seconds: float) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, *, now: float | None = None) -> RateLimitDecision:
        """Record an attempt against ``key`` and report whether it is permitted."""
        moment = time.monotonic() if now is None else now
        window = self._attempts[key]

        cutoff = moment - self._window_seconds
        while window and window[0] <= cutoff:
            window.popleft()

        if len(window) >= self._max_attempts:
            retry_after = window[0] + self._window_seconds - moment
            return RateLimitDecision(allowed=False, retry_after_seconds=max(1, int(retry_after)))

        window.append(moment)
        return RateLimitDecision(allowed=True, retry_after_seconds=0)

    def reset(self, key: str) -> None:
        """Clear a key's history, called after a successful authentication."""
        self._attempts.pop(key, None)

    def clear(self) -> None:
        self._attempts.clear()


# Five attempts per minute per username-and-address pair.
login_rate_limiter = SlidingWindowRateLimiter(max_attempts=5, window_seconds=60.0)
