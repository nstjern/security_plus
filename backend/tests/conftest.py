"""Shared fixtures.

API tests run against SQLite for speed. The schema is built from the models rather than by
running migrations; CI's dedicated migration job proves the models and migrations agree, so
the two cannot diverge unnoticed.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import Settings, get_settings
from app.core.rate_limit import login_rate_limiter
from app.db import tables  # noqa: F401 - imported so every table is registered
from app.db.session import get_db_session
from app.main import create_app
from app.models.progress import ProgressRecord
from app.services.question_bank import QuestionBank

USERNAME = "learner"
PASSWORD = "correct-horse-battery"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def bank(settings: Settings) -> QuestionBank:
    return QuestionBank.from_file(settings.questions_path)


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Iterator[None]:
    """The limiter is process-global, so one test's attempts must not affect another's."""
    login_rate_limiter.clear()
    yield
    login_rate_limiter.clear()


@pytest.fixture
def engine() -> Iterator[Engine]:
    # A single shared in-memory connection, so every session sees the same schema and data.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    app = create_app()

    def override_db_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db_session

    # The context manager runs lifespan, which loads the question bank.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def signed_in(client: TestClient) -> TestClient:
    response = client.post(
        "/api/auth/register",
        json={"username": USERNAME, "password": PASSWORD},
    )
    assert response.status_code == 201, response.text
    return client


@pytest.fixture
def csrf(signed_in: TestClient) -> dict[str, str]:
    return {"X-CSRF-Token": signed_in.cookies["sp_csrf"]}


@pytest.fixture
def records() -> dict[str, ProgressRecord]:
    """A learner who repeatedly misses one subject and slips once in another."""
    return {
        "clean-d01-q003": ProgressRecord(
            attempts=4, correct=1, incorrect=3, last_result="incorrect"
        ),
        "clean-d01-q004": ProgressRecord(attempts=1, incorrect=1, last_result="incorrect"),
        "clean-d02-q002": ProgressRecord(attempts=2, correct=2, last_result="correct"),
    }
