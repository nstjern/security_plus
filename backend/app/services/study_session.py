"""Study session rules: which questions, in what order, and how an answer is graded.

Grading is server-side. The browser is told only which choice was correct after it has
committed to an answer, so the answer key is never available to inspect beforehand.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from enum import StrEnum

from app.models.progress import AttemptResult
from app.models.question import Question
from app.services.question_bank import QuestionBank

DISPLAY_LETTERS = "abcd"

DEFAULT_PRACTICE_COUNT = 20
MAX_SESSION_QUESTIONS = 200


class StudyMode(StrEnum):
    all = "all"
    domain = "domain"
    chapter = "chapter"
    subject = "subject"
    objective = "objective"
    missed = "missed"
    practice = "practice"


class StudySessionError(ValueError):
    """Raised when a session cannot be built from the requested selection."""


@dataclass(frozen=True)
class DisplayChoice:
    letter: str
    text: str


@dataclass(frozen=True)
class PresentedQuestion:
    question: Question
    position: int
    total: int
    choices: list[DisplayChoice]


@dataclass(frozen=True)
class GradedAnswer:
    result: AttemptResult
    original_choice: str | None
    correct_display_letter: str
    correct_choice_text: str
    explanation: str
    correction_note: str | None


def select_question_ids(
    bank: QuestionBank,
    *,
    mode: StudyMode,
    filter_value: str | None = None,
    count: int | None = None,
    missed_question_ids: list[str] | None = None,
    shuffle: bool = True,
    seed: str | None = None,
) -> list[str]:
    """Choose the questions for a session and fix their order."""
    questions = _questions_for_mode(
        bank, mode=mode, filter_value=filter_value, missed_question_ids=missed_question_ids
    )
    if not questions:
        raise StudySessionError("No questions match that selection.")

    ordered = list(questions)
    if shuffle:
        _rng(seed).shuffle(ordered)

    if mode is StudyMode.practice:
        requested = count or DEFAULT_PRACTICE_COUNT
        ordered = ordered[: min(requested, len(ordered))]
    elif count is not None:
        ordered = ordered[: min(count, len(ordered))]

    return [question.id for question in ordered[:MAX_SESSION_QUESTIONS]]


def _questions_for_mode(
    bank: QuestionBank,
    *,
    mode: StudyMode,
    filter_value: str | None,
    missed_question_ids: list[str] | None,
) -> list[Question]:
    if mode in {StudyMode.all, StudyMode.practice}:
        return list(bank.questions)
    if mode is StudyMode.missed:
        return bank.filter(question_ids=missed_question_ids or [])

    if not filter_value:
        raise StudySessionError(f"Mode {mode.value!r} requires a filter value.")
    if mode is StudyMode.domain:
        return bank.filter(domain=filter_value)
    if mode is StudyMode.chapter:
        return bank.filter(chapter=filter_value)
    if mode is StudyMode.subject:
        return bank.filter(subject=filter_value)
    return bank.filter(objective=filter_value)


def choice_order(
    *,
    session_id: uuid.UUID,
    question: Question,
    shuffle_answers: bool,
) -> list[str]:
    """Return the question's own choice letters in the order they should be displayed.

    Derived from the session and question identifiers rather than stored, so the same
    ordering is reproduced on every request without extra persistence.
    """
    letters = sorted(question.choices)
    if shuffle_answers:
        _rng(f"{session_id}:{question.id}").shuffle(letters)
    return letters


def present_question(
    *,
    session_id: uuid.UUID,
    question: Question,
    position: int,
    total: int,
    shuffle_answers: bool,
) -> PresentedQuestion:
    order = choice_order(session_id=session_id, question=question, shuffle_answers=shuffle_answers)
    choices = [
        DisplayChoice(letter=display_letter, text=question.choices[original_letter])
        for display_letter, original_letter in zip(DISPLAY_LETTERS, order, strict=False)
    ]
    return PresentedQuestion(question=question, position=position, total=total, choices=choices)


def grade_answer(
    *,
    session_id: uuid.UUID,
    question: Question,
    display_choice: str | None,
    shuffle_answers: bool,
) -> GradedAnswer:
    """Translate a displayed letter back to the question's own lettering, then grade it."""
    order = choice_order(session_id=session_id, question=question, shuffle_answers=shuffle_answers)
    correct_display_letter = DISPLAY_LETTERS[order.index(question.answer)]

    if display_choice is None:
        result = AttemptResult.skipped
        original_choice = None
    else:
        original_choice = order[DISPLAY_LETTERS.index(display_choice)]
        result = (
            AttemptResult.correct if original_choice == question.answer else AttemptResult.incorrect
        )

    return GradedAnswer(
        result=result,
        original_choice=original_choice,
        correct_display_letter=correct_display_letter,
        correct_choice_text=question.correct_choice,
        explanation=question.explanation,
        correction_note=question.correction_note if question.corrected else None,
    )


def _rng(seed: str | None) -> random.Random:
    # Presentation order is a usability concern, not a security boundary.
    return random.Random(seed)  # noqa: S311
