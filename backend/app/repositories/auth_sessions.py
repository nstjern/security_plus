"""Server-side login session persistence.

Expiry is always evaluated in SQL. Comparing in Python would depend on whether the driver
returns an aware datetime, which differs between Postgres and SQLite.
"""

from __future__ import annotations

from datetime import timedelta

from sqlmodel import Session, col, select

from app.core.clock import utcnow
from app.db.tables import AuthSession


def create_auth_session(
    db: Session,
    *,
    user_id: int,
    token_hash: str,
    csrf_token: str,
    lifetime_hours: int,
) -> AuthSession:
    now = utcnow()
    auth_session = AuthSession(
        user_id=user_id,
        token_hash=token_hash,
        csrf_token=csrf_token,
        created_at=now,
        expires_at=now + timedelta(hours=lifetime_hours),
    )
    db.add(auth_session)
    db.commit()
    db.refresh(auth_session)
    return auth_session


def get_active_session(db: Session, token_hash: str) -> AuthSession | None:
    statement = select(AuthSession).where(
        AuthSession.token_hash == token_hash,
        col(AuthSession.expires_at) > utcnow(),
    )
    return db.exec(statement).first()


def delete_by_token_hash(db: Session, token_hash: str) -> None:
    auth_session = db.exec(select(AuthSession).where(AuthSession.token_hash == token_hash)).first()
    if auth_session is not None:
        db.delete(auth_session)
        db.commit()


def delete_expired(db: Session) -> int:
    """Housekeeping for sessions nobody logged out of."""
    expired = db.exec(select(AuthSession).where(col(AuthSession.expires_at) <= utcnow())).all()
    for auth_session in expired:
        db.delete(auth_session)
    db.commit()
    return len(expired)
