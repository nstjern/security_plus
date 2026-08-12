"""Shared fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app
from app.models.progress import ProgressRecord
from app.services.question_bank import QuestionBank


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def bank(settings: Settings) -> QuestionBank:
    return QuestionBank.from_file(settings.questions_path)


@pytest.fixture
def client() -> Iterator[TestClient]:
    # The context manager runs lifespan, which loads the question bank.
    with TestClient(create_app()) as test_client:
        yield test_client


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
