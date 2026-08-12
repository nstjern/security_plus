"""Health, readiness, and response hardening."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.routes import health


def test_liveness_does_not_depend_on_the_database(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_readiness_reports_ok_when_the_database_answers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health, "database_is_reachable", lambda: True)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "up"}


def test_readiness_reports_unavailable_when_the_database_is_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health, "database_is_reachable", lambda: False)
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}


def test_security_headers_are_applied_to_api_responses(client: TestClient) -> None:
    headers = client.get("/api/catalog").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in headers["Content-Security-Policy"]


def test_documentation_is_exempt_from_the_strict_content_policy(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers


def test_hsts_is_absent_outside_production(client: TestClient) -> None:
    assert "Strict-Transport-Security" not in client.get("/healthz").headers
