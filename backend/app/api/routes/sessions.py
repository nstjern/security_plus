"""Study sessions: create one, answer through it, end it."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import Bank, CsrfProtected, CurrentUser, DbSession, require_user_id
from app.api.schemas import (
    AnswerRequest,
    AnswerResponse,
    QuestionSummary,
    SessionCreateRequest,
    SessionQuestionResponse,
    SessionSummaryResponse,
    StudySessionResponse,
)
from app.db.tables import StudySession
from app.models.progress import AttemptResult
from app.repositories import progress as progress_repository
from app.repositories import study_sessions as study_session_repository
from app.services.study_session import (
    StudyMode,
    StudySessionError,
    grade_answer,
    present_question,
    select_question_ids,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

SESSION_COMPLETE = "This session has no questions left."

# Starlette renamed its 422 constant; the status code itself is stable across versions.
UNPROCESSABLE_CONTENT = 422


def _load_session(db: DbSession, session_id: uuid.UUID, user_id: int) -> StudySession:
    study_session = study_session_repository.get_study_session(db, session_id, user_id)
    if study_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return study_session


def _require_pending_question(study_session: StudySession) -> str:
    if study_session.status != study_session_repository.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=SESSION_COMPLETE)
    if study_session.current_index >= len(study_session.question_ids):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=SESSION_COMPLETE)
    return study_session.question_ids[study_session.current_index]


@router.post(
    "",
    response_model=StudySessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a study session",
)
def create_session(
    payload: SessionCreateRequest,
    context: CsrfProtected,
    db: DbSession,
    bank: Bank,
) -> StudySessionResponse:
    missed = (
        progress_repository.missed_question_ids(db, context.user_id)
        if payload.mode is StudyMode.missed
        else None
    )

    try:
        question_ids = select_question_ids(
            bank,
            mode=payload.mode,
            filter_value=payload.filter_value,
            count=payload.count,
            missed_question_ids=missed,
            shuffle=payload.shuffle_questions,
        )
    except StudySessionError as exc:
        raise HTTPException(status_code=UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

    study_session = study_session_repository.create_study_session(
        db,
        user_id=context.user_id,
        mode=payload.mode.value,
        filters={"value": payload.filter_value} if payload.filter_value else {},
        question_ids=question_ids,
        shuffle_answers=payload.shuffle_answers,
    )
    return StudySessionResponse.from_table(study_session)


@router.get("", response_model=list[StudySessionResponse], summary="Recent sessions")
def list_sessions(user: CurrentUser, db: DbSession) -> list[StudySessionResponse]:
    sessions = study_session_repository.list_study_sessions(db, require_user_id(user))
    return [StudySessionResponse.from_table(item) for item in sessions]


@router.get("/{session_id}", response_model=StudySessionResponse, summary="Read a session")
def read_session(session_id: uuid.UUID, user: CurrentUser, db: DbSession) -> StudySessionResponse:
    return StudySessionResponse.from_table(_load_session(db, session_id, require_user_id(user)))


@router.get(
    "/{session_id}/current-question",
    response_model=SessionQuestionResponse,
    summary="The question awaiting an answer",
)
def read_current_question(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
    bank: Bank,
) -> SessionQuestionResponse:
    study_session = _load_session(db, session_id, require_user_id(user))
    question_id = _require_pending_question(study_session)
    question = bank.require(question_id)

    presented = present_question(
        session_id=study_session.id,
        question=question,
        position=study_session.current_index + 1,
        total=len(study_session.question_ids),
        shuffle_answers=study_session.shuffle_answers,
    )
    return SessionQuestionResponse(
        position=presented.position,
        total=presented.total,
        question=QuestionSummary(
            id=question.id,
            domain=question.domain,
            chapter=question.grouping,
            subject=question.subject,
            objective=question.objective,
            question=question.question,
            choices={choice.letter: choice.text for choice in presented.choices},
        ),
    )


@router.post(
    "/{session_id}/answer",
    response_model=AnswerResponse,
    summary="Submit an answer and receive the explanation",
)
def submit_answer(
    session_id: uuid.UUID,
    payload: AnswerRequest,
    context: CsrfProtected,
    db: DbSession,
    bank: Bank,
) -> AnswerResponse:
    study_session = _load_session(db, session_id, context.user_id)
    question_id = _require_pending_question(study_session)
    question = bank.require(question_id)
    position = study_session.current_index + 1

    graded = grade_answer(
        session_id=study_session.id,
        question=question,
        display_choice=payload.choice,
        shuffle_answers=study_session.shuffle_answers,
    )

    progress_repository.record_attempt(
        db,
        user_id=context.user_id,
        question_id=question_id,
        result=graded.result,
        choice=graded.original_choice,
    )
    study_session_repository.record_answer(
        db,
        study_session=study_session,
        question_id=question_id,
        choice=payload.choice,
        result=graded.result.value,
    )

    return AnswerResponse(
        result=graded.result,
        correct_choice=graded.correct_display_letter,
        correct_choice_text=graded.correct_choice_text,
        explanation=graded.explanation,
        correction_note=graded.correction_note,
        position=position,
        total=len(study_session.question_ids),
        session_status=study_session.status,
        next_available=study_session.status == study_session_repository.ACTIVE,
    )


@router.post(
    "/{session_id}/end",
    response_model=StudySessionResponse,
    summary="End a session early",
)
def end_session(
    session_id: uuid.UUID,
    context: CsrfProtected,
    db: DbSession,
) -> StudySessionResponse:
    study_session = _load_session(db, session_id, context.user_id)
    return StudySessionResponse.from_table(
        study_session_repository.end_study_session(db, study_session)
    )


@router.get(
    "/{session_id}/summary",
    response_model=SessionSummaryResponse,
    summary="How the session went",
)
def read_session_summary(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> SessionSummaryResponse:
    study_session = _load_session(db, session_id, require_user_id(user))
    answers = study_session_repository.list_answers(db, study_session.id)

    tally = dict.fromkeys(AttemptResult, 0)
    for answer in answers:
        tally[AttemptResult(answer.result)] += 1

    graded = tally[AttemptResult.correct] + tally[AttemptResult.incorrect]
    return SessionSummaryResponse(
        session_id=study_session.id,
        status=study_session.status,
        total_questions=len(study_session.question_ids),
        answered=len(answers),
        correct=tally[AttemptResult.correct],
        incorrect=tally[AttemptResult.incorrect],
        skipped=tally[AttemptResult.skipped],
        accuracy=tally[AttemptResult.correct] / graded if graded else 0.0,
    )
