"""Configuration guardrails."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import DEVELOPMENT_SECRET, Environment, Settings


def test_production_refuses_the_development_secret() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
        Settings(environment=Environment.production, secret_key=DEVELOPMENT_SECRET)


def test_production_accepts_a_unique_secret() -> None:
    settings = Settings(environment=Environment.production, secret_key="a-unique-value")
    assert settings.is_production
    assert settings.secret_key.get_secret_value() == "a-unique-value"


def test_development_tolerates_the_default_secret() -> None:
    settings = Settings(environment=Environment.development)
    assert not settings.is_production


def test_secret_is_not_exposed_by_string_representation() -> None:
    settings = Settings(secret_key="super-secret-value")
    assert "super-secret-value" not in repr(settings)
