"""Authentication cookie handling.

The session cookie is ``HttpOnly`` so injected script cannot read it. The CSRF cookie
deliberately is not: the frontend must read it to echo the value in a request header.
Its value is worthless on its own, since the server compares it against the session record.
"""

from __future__ import annotations

from typing import Literal

from fastapi import Response

from app.core.config import Settings

# Lax still sends the cookie on top-level navigation, and localhost ports share a site,
# so the frontend dev server on another port is unaffected.
SAME_SITE_POLICY: Literal["lax"] = "lax"


def set_auth_cookies(
    response: Response,
    *,
    settings: Settings,
    session_token: str,
    csrf_token: str,
) -> None:
    max_age = settings.session_lifetime_hours * 3600
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=SAME_SITE_POLICY,
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=SAME_SITE_POLICY,
        path="/",
    )


def clear_auth_cookies(response: Response, *, settings: Settings) -> None:
    for name in (settings.session_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(
            name,
            path="/",
            httponly=name == settings.session_cookie_name,
            secure=settings.cookie_secure,
            samesite=SAME_SITE_POLICY,
        )
