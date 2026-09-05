"""Loading, validating, and querying the question bank."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

from pydantic import ValidationError

from app.models.question import Question, chapter_sort_key

CHAPTER_SOURCE_SECTION = "Chapter Quizzes"


class QuestionBankError(RuntimeError):
    """Raised when the question bank is missing, malformed, or internally inconsistent."""


class QuestionBank:
    """An immutable, in-memory view of the question bank."""

    def __init__(self, questions: Sequence[Question]) -> None:
        if not questions:
            raise QuestionBankError("The question bank must contain at least one question.")

        by_id: dict[str, Question] = {}
        for question in questions:
            if question.id in by_id:
                raise QuestionBankError(f"Duplicate question ID: {question.id}")
            by_id[question.id] = question

        self._questions: tuple[Question, ...] = tuple(questions)
        self._by_id = by_id

    @classmethod
    def from_file(cls, path: Path) -> QuestionBank:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise QuestionBankError(f"Question bank not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise QuestionBankError(f"Question bank is not valid JSON: {exc}") from exc

        if not isinstance(raw, list):
            raise QuestionBankError("The question bank must be a JSON list.")

        try:
            questions = [Question.model_validate(entry) for entry in raw]
        except ValidationError as exc:
            raise QuestionBankError(f"Question bank failed validation: {exc}") from exc
        return cls(questions)

    def __len__(self) -> int:
        return len(self._questions)

    def __iter__(self) -> Iterator[Question]:
        return iter(self._questions)

    @property
    def questions(self) -> tuple[Question, ...]:
        return self._questions

    def get(self, question_id: str) -> Question | None:
        return self._by_id.get(question_id)

    def require(self, question_id: str) -> Question:
        question = self._by_id.get(question_id)
        if question is None:
            raise KeyError(question_id)
        return question

    def domains(self) -> list[str]:
        return sorted({question.domain for question in self._questions})

    def chapters(self) -> list[str]:
        chapters = {
            question.grouping
            for question in self._questions
            if question.source_section == CHAPTER_SOURCE_SECTION
        }
        return sorted(chapters, key=chapter_sort_key)

    def subjects(self) -> list[str]:
        return sorted({question.subject for question in self._questions})

    def objectives(self) -> list[str]:
        return sorted({question.objective for question in self._questions})

    def filter(
        self,
        *,
        domain: str | None = None,
        chapter: str | None = None,
        subject: str | None = None,
        objective: str | None = None,
        question_ids: Iterable[str] | None = None,
    ) -> list[Question]:
        wanted_ids = set(question_ids) if question_ids is not None else None
        return [
            question
            for question in self._questions
            if (domain is None or question.domain == domain)
            and (chapter is None or question.grouping == chapter)
            and (subject is None or question.subject == subject)
            and (objective is None or question.objective == objective)
            and (wanted_ids is None or question.id in wanted_ids)
        ]
