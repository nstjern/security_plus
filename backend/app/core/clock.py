"""Time helpers.

Everything is written as UTC. Postgres returns timestamps with their offset intact; SQLite,
which the test suite uses, drops it. ``ensure_utc`` re-attaches it so application code never
has to compare a naive value against an aware one.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
