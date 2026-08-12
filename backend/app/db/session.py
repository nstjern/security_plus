"""Engine and session management.

The engine is created lazily so importing the application never requires a database.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, text
from sqlmodel import Session, create_engine

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_db_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    with Session(get_engine()) as session:
        yield session


def database_is_reachable() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        # A readiness probe reports failure; it never propagates one.
        return False
    return True
