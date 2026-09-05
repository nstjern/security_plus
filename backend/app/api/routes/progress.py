"""Cumulative progress across every session."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import Bank, CurrentUser, DbSession, require_user_id
from app.api.schemas import GroupStatsResponse, MissedQuestionSet, MissedQuestionsResponse, ProgressSummaryResponse
from app.repositories import progress as progress_repository
from app.services.statistics import group_results, lowest_performing_subjects

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/summary", response_model=ProgressSummaryResponse, summary="Accuracy by domain")
def read_summary(user: CurrentUser, db: DbSession, bank: Bank) -> ProgressSummaryResponse:
    records = progress_repository.load_records(db, require_user_id(user))
    domains = sorted(group_results(bank, records, field="domain").values(), key=lambda s: s.name)

    correct = sum(stats.correct for stats in domains)
    incorrect = sum(stats.incorrect for stats in domains)
    graded = correct + incorrect
    return ProgressSummaryResponse(
        attempts=sum(stats.attempts for stats in domains),
        correct=correct,
        incorrect=incorrect,
        skipped=sum(stats.skipped for stats in domains),
        graded=graded,
        accuracy=correct / graded if graded else 0.0,
        domains=[GroupStatsResponse.from_stats(stats) for stats in domains],
    )


@router.get(
    "/subjects",
    response_model=list[GroupStatsResponse],
    summary="Weakest subjects, least accurate first",
)
def read_weakest_subjects(
    user: CurrentUser,
    db: DbSession,
    bank: Bank,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[GroupStatsResponse]:
    records = progress_repository.load_records(db, require_user_id(user))
    subjects = lowest_performing_subjects(bank, records, limit=limit)
    return [GroupStatsResponse.from_stats(stats) for stats in subjects]


@router.get(
    "/missed",
    response_model=MissedQuestionsResponse,
    summary="Questions answered incorrectly at least once",
)
def read_missed_questions(user: CurrentUser, db: DbSession) -> MissedQuestionsResponse:
    user_id = require_user_id(user)
    all_ids = progress_repository.missed_question_ids(db, user_id)
    unresolved_ids = progress_repository.missed_question_ids(db, user_id, unresolved_only=True)
    return MissedQuestionsResponse(
        all=MissedQuestionSet(count=len(all_ids), question_ids=all_ids),
        unresolved=MissedQuestionSet(count=len(unresolved_ids), question_ids=unresolved_ids),
    )
