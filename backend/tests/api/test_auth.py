"""Registration, sign-in, CSRF, and rate limiting."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import PASSWORD, USERNAME

CREDENTIALS = {"username": USERNAME, "password": PASSWORD}


def test_registration_creates_an_account_and_signs_in(client: TestClient) -> None:
    response = client.post("/api/auth/register", json=CREDENTIALS)
    assert response.status_code == 201

    body = response.json()
    assert body["username"] == USERNAME
    assert "password" not in body
    assert "password_hash" not in body


def test_registration_sets_a_protected_session_cookie(client: TestClient) -> None:
    response = client.post("/api/auth/register", json=CREDENTIALS)
    cookies = response.headers.get_list("set-cookie")

    session_cookie = next(value for value in cookies if value.startswith("sp_session="))
    assert "HttpOnly" in session_cookie
    assert "SameSite=lax" in session_cookie
    assert "Path=/" in session_cookie


def test_the_csrf_cookie_is_readable_by_the_frontend(client: TestClient) -> None:
    """It must be readable to be echoed in a header; the server checks it against the session."""
    response = client.post("/api/auth/register", json=CREDENTIALS)
    csrf_cookie = next(
        value for value in response.headers.get_list("set-cookie") if value.startswith("sp_csrf=")
    )
    assert "HttpOnly" not in csrf_cookie


def test_duplicate_usernames_are_refused(signed_in: TestClient) -> None:
    response = signed_in.post("/api/auth/register", json=CREDENTIALS)
    assert response.status_code == 409


def test_short_passwords_are_refused(client: TestClient) -> None:
    response = client.post("/api/auth/register", json={"username": "someone", "password": "short"})
    assert response.status_code == 422


def test_usernames_with_unexpected_characters_are_refused(client: TestClient) -> None:
    response = client.post("/api/auth/register", json={"username": "a b", "password": PASSWORD})
    assert response.status_code == 422


def test_signing_in_with_the_right_password_succeeds(signed_in: TestClient) -> None:
    signed_in.cookies.clear()
    response = signed_in.post("/api/auth/login", json=CREDENTIALS)
    assert response.status_code == 200
    assert response.json()["username"] == USERNAME


def test_a_wrong_password_and_an_unknown_user_are_indistinguishable(
    signed_in: TestClient,
) -> None:
    """Differing responses would let an attacker enumerate valid usernames."""
    wrong_password = signed_in.post(
        "/api/auth/login", json={"username": USERNAME, "password": "not-the-password"}
    )
    unknown_user = signed_in.post(
        "/api/auth/login", json={"username": "nobody", "password": "not-the-password"}
    )

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_repeated_failures_are_rate_limited(client: TestClient) -> None:
    attempt = {"username": USERNAME, "password": "not-the-password"}
    statuses = [client.post("/api/auth/login", json=attempt).status_code for _ in range(6)]

    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429


def test_the_rate_limited_response_says_when_to_retry(client: TestClient) -> None:
    attempt = {"username": USERNAME, "password": "not-the-password"}
    for _ in range(6):
        response = client.post("/api/auth/login", json=attempt)
    assert int(response.headers["Retry-After"]) > 0


def test_a_successful_sign_in_clears_the_failure_count(signed_in: TestClient) -> None:
    for _ in range(4):
        signed_in.post("/api/auth/login", json={"username": USERNAME, "password": "wrong"})

    assert signed_in.post("/api/auth/login", json=CREDENTIALS).status_code == 200
    assert signed_in.post("/api/auth/login", json=CREDENTIALS).status_code == 200


def test_the_current_user_requires_a_session(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_the_current_user_is_returned_when_signed_in(signed_in: TestClient) -> None:
    assert signed_in.get("/api/auth/me").json()["username"] == USERNAME


def test_a_forged_session_cookie_is_rejected(client: TestClient) -> None:
    client.cookies.set("sp_session", "a-token-that-was-never-issued")
    assert client.get("/api/auth/me").status_code == 401


def test_signing_out_without_the_csrf_header_is_refused(signed_in: TestClient) -> None:
    assert signed_in.post("/api/auth/logout").status_code == 403


def test_signing_out_with_a_wrong_csrf_token_is_refused(signed_in: TestClient) -> None:
    response = signed_in.post("/api/auth/logout", headers={"X-CSRF-Token": "not-the-token"})
    assert response.status_code == 403


def test_signing_out_revokes_the_session(signed_in: TestClient, csrf: dict[str, str]) -> None:
    assert signed_in.post("/api/auth/logout", headers=csrf).status_code == 204
    assert signed_in.get("/api/auth/me").status_code == 401


def test_a_revoked_session_cannot_be_replayed(signed_in: TestClient, csrf: dict[str, str]) -> None:
    """Server-side revocation is why this is a session, not a self-contained token."""
    stolen_token = signed_in.cookies["sp_session"]
    signed_in.post("/api/auth/logout", headers=csrf)

    signed_in.cookies.set("sp_session", stolen_token)
    assert signed_in.get("/api/auth/me").status_code == 401
