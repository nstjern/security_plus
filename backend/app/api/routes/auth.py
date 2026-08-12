"""Registration, login, logout, and the current user."""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.cookies import clear_auth_cookies, set_auth_cookies
from app.api.deps import AppSettings, CsrfProtected, CurrentUser, DbSession, require_user_id
from app.api.schemas import LoginRequest, RegisterRequest, UserResponse
from app.core.config import Settings
from app.core.rate_limit import login_rate_limiter
from app.core.security import (
    generate_csrf_token,
    generate_session_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    verify_password,
)
from app.db.tables import User
from app.repositories import auth_sessions as auth_session_repository
from app.repositories import users as user_repository

router = APIRouter(prefix="/auth", tags=["auth"])

# One message for every failure, so responses cannot be used to discover valid usernames.
INVALID_CREDENTIALS = "Invalid username or password"


@lru_cache(maxsize=1)
def _timing_equalizer_hash() -> str:
    """A real hash to verify against when the username does not exist.

    Without it, an unknown username would return noticeably faster than a known one, which
    turns response time into a user-enumeration oracle.
    """
    return hash_password("a-password-that-is-never-valid")


def _start_session(
    db: DbSession,
    response: Response,
    settings: Settings,
    user: User,
) -> None:
    # Sessions nobody logged out of are cleared here; there is no scheduler to do it.
    auth_session_repository.delete_expired(db)

    session_token = generate_session_token()
    csrf_token = generate_csrf_token()
    auth_session_repository.create_auth_session(
        db,
        user_id=require_user_id(user),
        token_hash=hash_token(session_token, key=settings.secret_key.get_secret_value()),
        csrf_token=csrf_token,
        lifetime_hours=settings.session_lifetime_hours,
    )
    set_auth_cookies(
        response,
        settings=settings,
        session_token=session_token,
        csrf_token=csrf_token,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and sign in",
)
def register(
    payload: RegisterRequest,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> UserResponse:
    if user_repository.get_user_by_username(db, payload.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That username is already taken",
        )

    user = user_repository.create_user(
        db,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    _start_session(db, response, settings, user)
    return UserResponse.from_user(user)


@router.post("/login", response_model=UserResponse, summary="Sign in")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> UserResponse:
    client_address = request.client.host if request.client else "unknown"
    rate_limit_key = f"{payload.username}:{client_address}"

    decision = login_rate_limiter.check(rate_limit_key)
    if not decision.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many sign-in attempts. Try again shortly.",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )

    user = user_repository.get_user_by_username(db, payload.username)
    stored_hash = user.password_hash if user is not None else _timing_equalizer_hash()
    password_matches = verify_password(stored_hash, payload.password)

    if user is None or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
        )

    if password_needs_rehash(user.password_hash):
        user_repository.update_password_hash(db, user, hash_password(payload.password))

    login_rate_limiter.reset(rate_limit_key)
    _start_session(db, response, settings, user)
    return UserResponse.from_user(user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out and revoke the session",
)
def logout(context: CsrfProtected, db: DbSession, settings: AppSettings) -> Response:
    # Revoked server-side, so the credential cannot be replayed even if it was captured.
    auth_session_repository.delete_by_token_hash(db, context.auth_session.token_hash)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_auth_cookies(response, settings=settings)
    return response


@router.get("/me", response_model=UserResponse, summary="The signed-in user")
def read_current_user(user: CurrentUser) -> UserResponse:
    return UserResponse.from_user(user)
