"""Progress and analytics models shared by the statistics and review services."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AttemptResult(StrEnum):
    correct = "correct"
    incorrect = "incorrect"
    skipped = "skipped"


class ProgressRecord(BaseModel):
    """Per-question totals accumulated across every session."""

    attempts: int = 0
    correct: int = 0
    incorrect: int = 0
    skipped: int = 0
    last_result: AttemptResult | None = None
    # Kept so feedback can name the distractor that was chosen, not just the right answer.
    last_answer: str | None = None

    @property
    def graded(self) -> int:
        """Skipped questions are excluded; only answered questions are scored."""
        return self.correct + self.incorrect


class GroupStats(BaseModel):
    """Aggregated totals for one domain, subject, or chapter."""

    name: str
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0
    skipped: int = 0

    @property
    def graded(self) -> int:
        return self.correct + self.incorrect

    @property
    def accuracy(self) -> float:
        return self.correct / self.graded if self.graded else 0.0

    @property
    def error_rate(self) -> float:
        return self.incorrect / self.graded if self.graded else 0.0


class WeakArea(BaseModel):
    """A domain-and-subject pairing the learner has missed at least once."""

    domain: str
    subject: str
    attempts: int = 0
    correct: int = 0
    incorrect: int = 0
    skipped: int = 0
    missed_question_ids: list[str] = Field(default_factory=list)

    @property
    def graded(self) -> int:
        return self.correct + self.incorrect

    @property
    def accuracy(self) -> float:
        return self.correct / self.graded if self.graded else 0.0

    @property
    def error_rate(self) -> float:
        return self.incorrect / self.graded if self.graded else 0.0

    @property
    def weakness_score(self) -> float:
        """Combine volume and rate so repeated misses outrank isolated mistakes."""
        return self.incorrect * self.error_rate
