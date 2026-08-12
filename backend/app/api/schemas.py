"""Request and response models.

These are the API's public contract. Keeping them separate from the domain models means an
internal refactor cannot silently change what clients receive.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.question import Question


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
