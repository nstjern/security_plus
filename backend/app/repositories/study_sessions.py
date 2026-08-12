"""Study session persistence."""

from __future__ import annotations

import uuid

from sqlmodel import Session, col, select

from app.core.clock import utcnow
from app.db.tables import SessionAnswer, StudySession

ACTIVE = "active"
FINISHED = "finished"
ENDED = "ended"


def create_study_session(
    db: Session,
    *,
    user_id: int,
    mode: str,
    filters: dict[str, str],
    question_ids: list[str],
    shuffle_answers: bool,
) -> StudySession:
    study_session = StudySession(
        user_id=user_id,
        mode=mode,
        filters=filters,
        question_ids=question_ids,
        shuffle_answers=shuffle_answers,
        status=ACTIVE,
    )
    db.add(study_session)
    db.commit()
    db.refresh(study_session)
    return study_session


def get_study_session(db: Session, session_id: uuid.UUID, user_id: int) -> StudySession | None:
    """Scoped by user so one learner can never read another's session."""
    statement = select(StudySession).where(
        StudySession.id == session_id,
        StudySession.user_id == user_id,
    )
    return db.exec(statement).first()


def list_study_sessions(db: Session, user_id: int, *, limit: int = 20) -> list[StudySession]:
    statement = (
        select(StudySession)
        .where(StudySession.user_id == user_id)
        .order_by(col(StudySession.created_at).desc())
        .limit(limit)
    )
    return list(db.exec(statement).all())


def record_answer(
    db: Session,
    *,
    study_session: StudySession,
    question_id: str,
    choice: str | None,
    result: str,
) -> SessionAnswer:
    answer = SessionAnswer(
        session_id=study_session.id,
        question_id=question_id,
        user_choice=choice,
        result=result,
    )
    study_session.current_index += 1
    if study_session.current_index >= len(study_session.question_ids):
        study_session.status = FINISHED
        study_session.ended_at = utcnow()

    db.add(answer)
    db.add(study_session)
    db.commit()
    db.refresh(answer)
    db.refresh(study_session)
    return answer


def end_study_session(db: Session, study_session: StudySession) -> StudySession:
    if study_session.status == ACTIVE:
        study_session.status = ENDED
        study_session.ended_at = utcnow()
        db.add(study_session)
        db.commit()
        db.refresh(study_session)
    return study_session


def list_answers(db: Session, session_id: uuid.UUID) -> list[SessionAnswer]:
    statement = (
        select(SessionAnswer)
        .where(SessionAnswer.session_id == session_id)
        .order_by(col(SessionAnswer.answered_at))
    )
    return list(db.exec(statement).all())
