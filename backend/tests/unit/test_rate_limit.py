"""Sliding-window rate limiting."""

from __future__ import annotations

import pytest

from app.core.rate_limit import SlidingWindowRateLimiter


def test_attempts_within_the_limit_are_allowed() -> None:
    limiter = SlidingWindowRateLimiter(max_attempts=3, window_seconds=60)
    assert all(limiter.check("key", now=0).allowed for _ in range(3))


def test_the_attempt_after_the_limit_is_refused() -> None:
    limiter = SlidingWindowRateLimiter(max_attempts=3, window_seconds=60)
    for _ in range(3):
        limiter.check("key", now=0)

    decision = limiter.check("key", now=1)
    assert not decision.allowed
    assert decision.retry_after_seconds > 0


def test_keys_are_counted_independently() -> None:
    limiter = SlidingWindowRateLimiter(max_attempts=1, window_seconds=60)
    assert limiter.check("first", now=0).allowed
    assert limiter.check("second", now=0).allowed
    assert not limiter.check("first", now=0).allowed


def test_attempts_older_than_the_window_stop_counting() -> None:
    limiter = SlidingWindowRateLimiter(max_attempts=2, window_seconds=60)
    limiter.check("key", now=0)
    limiter.check("key", now=1)
    assert not limiter.check("key", now=30).allowed
    assert limiter.check("key", now=120).allowed


def test_reset_clears_a_single_key() -> None:
    limiter = SlidingWindowRateLimiter(max_attempts=1, window_seconds=60)
    limiter.check("key", now=0)
    limiter.reset("key")
    assert limiter.check("key", now=0).allowed


def test_clear_discards_every_key() -> None:
    limiter = SlidingWindowRateLimiter(max_attempts=1, window_seconds=60)
    limiter.check("first", now=0)
    limiter.check("second", now=0)
    limiter.clear()
    assert limiter.check("first", now=0).allowed
    assert limiter.check("second", now=0).allowed


def test_a_limiter_that_allows_nothing_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        SlidingWindowRateLimiter(max_attempts=0, window_seconds=60)


def test_the_default_clock_is_used_when_no_time_is_supplied() -> None:
    limiter = SlidingWindowRateLimiter(max_attempts=1, window_seconds=60)
    assert limiter.check("key").allowed
    assert not limiter.check("key").allowed
