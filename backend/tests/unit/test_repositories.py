"""Repository behaviour that the HTTP tests do not reach directly."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import Engine
from sqlmodel import Session

from app.core.clock import utcnow
from app.models.progress import AttemptResult
from app.repositories import auth_sessions as auth_session_repository
from app.repositories import progress as progress_repository
from app.repositories import users as user_repository


@pytest.fixture
def db(engine: Engine) -> Session:
    return Session(engine)


@pytest.fixture
def user_id(db: Session) -> int:
    user = user_repository.create_user(db, username="learner", password_hash="hash")
    assert user.id is not None
    return user.id


def test_users_are_found_by_name_and_id(db: Session, user_id: int) -> None:
    assert user_repository.get_user_by_username(db, "learner") is not None
    assert user_repository.get_user_by_id(db, user_id) is not None


def test_an_unknown_username_returns_nothing(db: Session) -> None:
    assert user_repository.get_user_by_username(db, "nobody") is None


def test_a_password_hash_can_be_replaced(db: Session, user_id: int) -> None:
    user = user_repository.get_user_by_id(db, user_id)
    assert user is not None

    user_repository.update_password_hash(db, user, "a-new-hash")
    refreshed = user_repository.get_user_by_id(db, user_id)
    assert refreshed is not None
    assert refreshed.password_hash == "a-new-hash"


def test_an_active_session_is_found_by_its_token_digest(db: Session, user_id: int) -> None:
    auth_session_repository.create_auth_session(
        db, user_id=user_id, token_hash="digest", csrf_token="csrf", lifetime_hours=1
    )
    assert auth_session_repository.get_active_session(db, "digest") is not None


def test_an_expired_session_is_not_returned(db: Session, user_id: int) -> None:
    auth_session_repository.create_auth_session(
        db, user_id=user_id, token_hash="stale", csrf_token="csrf", lifetime_hours=-1
    )
    assert auth_session_repository.get_active_session(db, "stale") is None


def test_expired_sessions_are_purged_and_active_ones_kept(db: Session, user_id: int) -> None:
    auth_session_repository.create_auth_session(
        db, user_id=user_id, token_hash="stale", csrf_token="csrf", lifetime_hours=-1
    )
    auth_session_repository.create_auth_session(
        db, user_id=user_id, token_hash="fresh", csrf_token="csrf", lifetime_hours=1
    )

    assert auth_session_repository.delete_expired(db) == 1
    assert auth_session_repository.get_active_session(db, "fresh") is not None


def test_deleting_an_absent_session_is_harmless(db: Session) -> None:
    auth_session_repository.delete_by_token_hash(db, "never-existed")


def test_session_expiry_is_derived_from_the_configured_lifetime(db: Session, user_id: int) -> None:
    auth_session = auth_session_repository.create_auth_session(
        db, user_id=user_id, token_hash="digest", csrf_token="csrf", lifetime_hours=6
    )
    lifetime = auth_session.expires_at - auth_session.created_at
    assert timedelta(hours=5, minutes=59) < lifetime < timedelta(hours=6, minutes=1)
    assert auth_session.created_at <= utcnow().replace(tzinfo=auth_session.created_at.tzinfo)


def test_attempts_accumulate_across_answers(db: Session, user_id: int) -> None:
    for result in (AttemptResult.correct, AttemptResult.incorrect, AttemptResult.skipped):
        progress_repository.record_attempt(
            db, user_id=user_id, question_id="clean-d01-q001", result=result, choice="a"
        )

    record = progress_repository.load_records(db, user_id)["clean-d01-q001"]
    assert record.attempts == 3
    assert (record.correct, record.incorrect, record.skipped) == (1, 1, 1)
    assert record.last_result is AttemptResult.skipped


def test_the_chosen_answer_is_remembered(db: Session, user_id: int) -> None:
    """Stored so the review guide can later say which distractor was tempting."""
    progress_repository.record_attempt(
        db,
        user_id=user_id,
        question_id="clean-d01-q001",
        result=AttemptResult.incorrect,
        choice="c",
    )
    assert progress_repository.load_records(db, user_id)["clean-d01-q001"].last_answer == "c"


def test_missed_questions_are_ordered_by_how_often_they_were_missed(
    db: Session, user_id: int
) -> None:
    for _ in range(3):
        progress_repository.record_attempt(
            db, user_id=user_id, question_id="often", result=AttemptResult.incorrect
        )
    progress_repository.record_attempt(
        db, user_id=user_id, question_id="once", result=AttemptResult.incorrect
    )
    progress_repository.record_attempt(
        db, user_id=user_id, question_id="never", result=AttemptResult.correct
    )

    assert progress_repository.missed_question_ids(db, user_id) == ["often", "once"]


def test_progress_is_scoped_to_one_learner(db: Session, user_id: int) -> None:
    other = user_repository.create_user(db, username="other", password_hash="hash")
    assert other.id is not None

    progress_repository.record_attempt(
        db, user_id=user_id, question_id="clean-d01-q001", result=AttemptResult.incorrect
    )
    assert progress_repository.load_records(db, other.id) == {}
