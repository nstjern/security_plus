"""Database tables.

Only learner-owned data lives here. The question bank stays in version-controlled JSON
(see contracts/adr/0003-question-bank-stays-in-json.md).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _timestamp_column(*, nullable: bool = False) -> Column[datetime]:
    """Store timestamps with their offset so comparisons survive a timezone change."""
    return Column(DateTime(timezone=True), nullable=nullable)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=80)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=_utcnow, sa_column=_timestamp_column())


class QuestionProgress(SQLModel, table=True):
    __tablename__ = "question_progress"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_progress_user_question"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    question_id: str = Field(max_length=64, index=True)
    attempts: int = Field(default=0)
    correct: int = Field(default=0)
    incorrect: int = Field(default=0)
    skipped: int = Field(default=0)
    last_result: str | None = Field(default=None, max_length=16)
    last_answer: str | None = Field(default=None, max_length=1)
    updated_at: datetime = Field(default_factory=_utcnow, sa_column=_timestamp_column())


class StudySession(SQLModel, table=True):
    __tablename__ = "study_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    mode: str = Field(max_length=32)
    filters: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    question_ids: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    current_index: int = Field(default=0)
    status: str = Field(default="active", max_length=16)
    shuffle_answers: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow, sa_column=_timestamp_column())
    ended_at: datetime | None = Field(default=None, sa_column=_timestamp_column(nullable=True))


class SessionAnswer(SQLModel, table=True):
    __tablename__ = "session_answers"

    id: int | None = Field(default=None, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="study_sessions.id", index=True)
    question_id: str = Field(max_length=64)
    user_choice: str | None = Field(default=None, max_length=1)
    result: str = Field(max_length=16)
    answered_at: datetime = Field(default_factory=_utcnow, sa_column=_timestamp_column())
