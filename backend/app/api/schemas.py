"""Request and response models.

These are the API's public contract. Keeping them separate from the domain models means an
internal refactor cannot silently change what clients receive.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.clock import ensure_utc
from app.db.tables import StudySession, User
from app.models.progress import AttemptResult, GroupStats
from app.models.question import Question
from app.services.study_session import StudyMode

# Minimum length is the control that matters most for passphrases; complexity rules push
# users toward predictable substitutions. See SECURITY.md.
MINIMUM_PASSWORD_LENGTH = 12


class MissedScope(StrEnum):
    all = "all"
    unresolved = "unresolved"


class HealthResponse(BaseModel):
    status: str
    version: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


class CatalogResponse(BaseModel):
    """Every value that can be used to filter a study session."""

    domains: list[str]
    chapters: list[str]
    subjects: list[str]
    objectives: list[str]
    question_count: int


class QuestionSummary(BaseModel):
    """A question as sent to an unauthenticated client.

    The answer, explanation, and correction note are deliberately omitted; they are revealed
    only in the response to a submitted answer.
    """

    id: str
    domain: str
    chapter: str
    subject: str
    objective: str
    question: str
    choices: dict[str, str]

    @classmethod
    def from_question(cls, question: Question) -> QuestionSummary:
        return cls(
            id=question.id,
            domain=question.domain,
            chapter=question.grouping,
            subject=question.subject,
            objective=question.objective,
            question=question.question,
            choices=question.choices,
        )


class QuestionPage(BaseModel):
    items: list[QuestionSummary]
    total: int
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=MINIMUM_PASSWORD_LENGTH, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> UserResponse:
        if user.id is None:  # pragma: no cover - persisted users always have an id
            raise ValueError("user has not been persisted")
        return cls(id=user.id, username=user.username, created_at=ensure_utc(user.created_at))


class SessionCreateRequest(BaseModel):
    mode: StudyMode
    # The value the mode filters on: a domain, chapter, subject, or objective name.
    filter_value: str | None = Field(default=None, max_length=200)
    missed_scope: MissedScope = MissedScope.all
    count: int | None = Field(default=None, ge=1, le=200)
    shuffle_answers: bool = False
    shuffle_questions: bool = True


class StudySessionResponse(BaseModel):
    id: uuid.UUID
    mode: str
    filters: dict[str, str]
    total_questions: int
    answered: int
    status: str
    shuffle_answers: bool
    created_at: datetime
    ended_at: datetime | None

    @classmethod
    def from_table(cls, study_session: StudySession) -> StudySessionResponse:
        return cls(
            id=study_session.id,
            mode=study_session.mode,
            filters=study_session.filters,
            total_questions=len(study_session.question_ids),
            answered=study_session.current_index,
            status=study_session.status,
            shuffle_answers=study_session.shuffle_answers,
            created_at=ensure_utc(study_session.created_at),
            ended_at=ensure_utc(study_session.ended_at) if study_session.ended_at else None,
        )


class SessionQuestionResponse(BaseModel):
    position: int
    total: int
    question: QuestionSummary


class AnswerRequest(BaseModel):
    """A displayed letter, or null to skip the question."""

    choice: Literal["a", "b", "c", "d"] | None = None


class AnswerResponse(BaseModel):
    result: AttemptResult
    correct_choice: str
    correct_choice_text: str
    explanation: str
    correction_note: str | None
    position: int
    total: int
    session_status: str
    next_available: bool


class SessionSummaryResponse(BaseModel):
    session_id: uuid.UUID
    status: str
    total_questions: int
    answered: int
    correct: int
    incorrect: int
    skipped: int
    accuracy: float


class GroupStatsResponse(BaseModel):
    name: str
    attempts: int
    correct: int
    incorrect: int
    skipped: int
    graded: int
    accuracy: float

    @classmethod
    def from_stats(cls, stats: GroupStats) -> GroupStatsResponse:
        return cls(
            name=stats.name,
            attempts=stats.attempts,
            correct=stats.correct,
            incorrect=stats.incorrect,
            skipped=stats.skipped,
            graded=stats.graded,
            accuracy=stats.accuracy,
        )


class ProgressSummaryResponse(BaseModel):
    attempts: int
    correct: int
    incorrect: int
    skipped: int
    graded: int
    accuracy: float
    domains: list[GroupStatsResponse]


class MissedQuestionSet(BaseModel):
    count: int
    question_ids: list[str]


class MissedQuestionsResponse(BaseModel):
    all: MissedQuestionSet
    unresolved: MissedQuestionSet
