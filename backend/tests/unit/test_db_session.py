"""Database session plumbing."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, create_engine

from app.db import session as session_module


@pytest.fixture
def sqlite_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_module, "get_engine", lambda: create_engine("sqlite://"))


@pytest.mark.usefixtures("sqlite_engine")
def test_dependency_yields_a_usable_session() -> None:
    generator = session_module.get_db_session()
    db_session = next(generator)
    assert isinstance(db_session, Session)
    generator.close()


@pytest.mark.usefixtures("sqlite_engine")
def test_reachability_check_succeeds_against_a_live_engine() -> None:
    assert session_module.database_is_reachable() is True


def test_reachability_check_reports_failure_instead_of_raising(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unreachable() -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(session_module, "get_engine", unreachable)
    assert session_module.database_is_reachable() is False
