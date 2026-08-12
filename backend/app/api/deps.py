"""Shared FastAPI dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.core.security import hash_token, tokens_match
from app.db.session import get_db_session
from app.db.tables import AuthSession, User
from app.repositories import auth_sessions as auth_session_repository
from app.repositories import users as user_repository
from app.services.question_bank import QuestionBank

CSRF_HEADER = "X-CSRF-Token"

NOT_AUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
)


@dataclass(frozen=True)
class AuthContext:
    user: User
    auth_session: AuthSession

    @property
    def user_id(self) -> int:
        return require_user_id(self.user)


def require_user_id(user: User) -> int:
    """Narrow the optional primary key; an authenticated user is always persisted."""
    if user.id is None:  # pragma: no cover - unreachable for a loaded row
        raise ValueError("user has not been persisted")
    return user.id


def get_question_bank(request: Request) -> QuestionBank:
    """Return the bank loaded once during application startup."""
    bank: QuestionBank = request.app.state.question_bank
    return bank


def get_auth_context(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthContext:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise NOT_AUTHENTICATED

    auth_session = auth_session_repository.get_active_session(
        db, hash_token(token, key=settings.secret_key.get_secret_value())
    )
    if auth_session is None:
        raise NOT_AUTHENTICATED

    user = user_repository.get_user_by_id(db, auth_session.user_id)
    if user is None:
        raise NOT_AUTHENTICATED

    return AuthContext(user=user, auth_session=auth_session)


def get_current_user(context: Annotated[AuthContext, Depends(get_auth_context)]) -> User:
    return context.user


def require_csrf(
    request: Request,
    context: Annotated[AuthContext, Depends(get_auth_context)],
) -> AuthContext:
    """Verify the double-submit token on state-changing requests."""
    submitted = request.headers.get(CSRF_HEADER, "")
    if not submitted or not tokens_match(submitted, context.auth_session.csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid CSRF token",
        )
    return context


CurrentUser = Annotated[User, Depends(get_current_user)]
CsrfProtected = Annotated[AuthContext, Depends(require_csrf)]
DbSession = Annotated[Session, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]
Bank = Annotated[QuestionBank, Depends(get_question_bank)]
