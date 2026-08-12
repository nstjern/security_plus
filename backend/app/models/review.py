"""Structured review-guide models.

The CLI rendered the guide directly to strings. Returning structured data instead lets the
API, a future export format, and a later tutor layer share one representation.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReviewConcept(BaseModel):
    question_id: str
    objective: str
    chapter: str
    prompt: str
    correct_choice: str
    explanation: str
    correction_note: str | None = None


class DomainPriority(BaseModel):
    rank: int
    domain: str
    accuracy: float
    incorrect: int
    weakness_score: float


class FocusArea(BaseModel):
    rank: int
    domain: str
    subject: str
    accuracy: float
    correct: int
    incorrect: int
    weakness_score: float
    concepts: list[ReviewConcept] = Field(default_factory=list)


class ReviewGuide(BaseModel):
    generated_at: datetime
    total_graded: int
    total_correct: int
    total_incorrect: int
    overall_accuracy: float
    priority_domains: list[DomainPriority] = Field(default_factory=list)
    focus_areas: list[FocusArea] = Field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.focus_areas
