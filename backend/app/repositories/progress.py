"""Per-question progress persistence.

Rows are keyed by ``(user_id, question_id)``. The services layer works with the domain's
``ProgressRecord``, so the table shape stays an implementation detail.
"""

from __future__ import annotations

from sqlmodel import Session, col, select

from app.core.clock import utcnow
from app.db.tables import QuestionProgress
from app.models.progress import AttemptResult, ProgressRecord


def _to_record(row: QuestionProgress) -> ProgressRecord:
    return ProgressRecord(
        attempts=row.attempts,
        correct=row.correct,
        incorrect=row.incorrect,
        skipped=row.skipped,
        last_result=AttemptResult(row.last_result) if row.last_result else None,
        last_answer=row.last_answer,
    )


def load_records(db: Session, user_id: int) -> dict[str, ProgressRecord]:
    rows = db.exec(select(QuestionProgress).where(QuestionProgress.user_id == user_id)).all()
    return {row.question_id: _to_record(row) for row in rows}


def _get_row(db: Session, user_id: int, question_id: str) -> QuestionProgress | None:
    statement = select(QuestionProgress).where(
        QuestionProgress.user_id == user_id,
        QuestionProgress.question_id == question_id,
    )
    return db.exec(statement).first()


def record_attempt(
    db: Session,
    *,
    user_id: int,
    question_id: str,
    result: AttemptResult,
    choice: str | None = None,
) -> ProgressRecord:
    """Add one attempt to the learner's totals for a question."""
    row = _get_row(db, user_id, question_id)
    if row is None:
        row = QuestionProgress(user_id=user_id, question_id=question_id)

    row.attempts += 1
    if result is AttemptResult.correct:
        row.correct += 1
    elif result is AttemptResult.incorrect:
        row.incorrect += 1
    else:
        row.skipped += 1

    row.last_result = result.value
    row.last_answer = choice
    row.updated_at = utcnow()

    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_record(row)


def missed_question_ids(db: Session, user_id: int, *, unresolved_only: bool = False) -> list[str]:
    statement = select(QuestionProgress.question_id).where(
        QuestionProgress.user_id == user_id,
        col(QuestionProgress.incorrect) > 0,
    )
    if unresolved_only:
        statement = statement.where(col(QuestionProgress.correct) == 0)
    statement = statement.order_by(col(QuestionProgress.incorrect).desc())
    return list(db.exec(statement).all())
