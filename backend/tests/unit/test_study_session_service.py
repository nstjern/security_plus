"""Session composition, choice ordering, and grading."""

from __future__ import annotations

import uuid

import pytest

from app.core.constants import DOMAIN_NAMES
from app.models.progress import AttemptResult
from app.services.question_bank import QuestionBank
from app.services.study_session import (
    DISPLAY_LETTERS,
    StudyMode,
    StudySessionError,
    choice_order,
    grade_answer,
    present_question,
    select_question_ids,
)

SESSION_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")
OTHER_SESSION_ID = uuid.UUID("99999999-2222-3333-4444-555555555555")


def test_all_mode_selects_the_whole_bank(bank: QuestionBank) -> None:
    assert len(select_question_ids(bank, mode=StudyMode.all)) == len(bank)


def test_ordering_is_reproducible_for_a_given_seed(bank: QuestionBank) -> None:
    first = select_question_ids(bank, mode=StudyMode.all, seed="seed-a")
    second = select_question_ids(bank, mode=StudyMode.all, seed="seed-a")
    third = select_question_ids(bank, mode=StudyMode.all, seed="seed-b")
    assert first == second
    assert first != third


def test_unshuffled_selection_preserves_bank_order(bank: QuestionBank) -> None:
    ids = select_question_ids(bank, mode=StudyMode.all, shuffle=False)
    assert ids == [question.id for question in bank.questions]


def test_domain_mode_narrows_to_that_domain(bank: QuestionBank) -> None:
    ids = select_question_ids(bank, mode=StudyMode.domain, filter_value=DOMAIN_NAMES[1])
    assert ids
    assert all(bank.require(question_id).domain == DOMAIN_NAMES[1] for question_id in ids)


def test_subject_mode_narrows_to_that_subject(bank: QuestionBank) -> None:
    subject = bank.require("clean-d01-q003").subject
    ids = select_question_ids(bank, mode=StudyMode.subject, filter_value=subject)
    assert all(bank.require(question_id).subject == subject for question_id in ids)


def test_missed_mode_uses_only_the_supplied_questions(bank: QuestionBank) -> None:
    missed = ["clean-d01-q003", "clean-d01-q004"]
    assert sorted(select_question_ids(bank, mode=StudyMode.missed, missed_question_ids=missed)) == (
        sorted(missed)
    )


def test_practice_mode_honours_the_requested_count(bank: QuestionBank) -> None:
    assert len(select_question_ids(bank, mode=StudyMode.practice, count=7)) == 7


def test_practice_mode_defaults_to_twenty_questions(bank: QuestionBank) -> None:
    assert len(select_question_ids(bank, mode=StudyMode.practice)) == 20


def test_practice_mode_cannot_exceed_the_bank(bank: QuestionBank) -> None:
    assert len(select_question_ids(bank, mode=StudyMode.practice, count=200)) == len(bank)


def test_a_filtered_mode_without_a_value_is_rejected(bank: QuestionBank) -> None:
    with pytest.raises(StudySessionError, match="requires a filter value"):
        select_question_ids(bank, mode=StudyMode.subject)


def test_a_selection_matching_nothing_is_rejected(bank: QuestionBank) -> None:
    with pytest.raises(StudySessionError, match="No questions match"):
        select_question_ids(bank, mode=StudyMode.subject, filter_value="Nonexistent")


def test_missed_mode_with_nothing_missed_is_rejected(bank: QuestionBank) -> None:
    with pytest.raises(StudySessionError, match="No questions match"):
        select_question_ids(bank, mode=StudyMode.missed, missed_question_ids=[])


def test_unshuffled_choices_keep_their_original_lettering(bank: QuestionBank) -> None:
    question = bank.require("clean-d01-q001")
    assert choice_order(session_id=SESSION_ID, question=question, shuffle_answers=False) == list(
        "abcd"
    )


def test_shuffled_choice_order_is_stable_for_a_session_and_question(bank: QuestionBank) -> None:
    question = bank.require("clean-d01-q001")
    first = choice_order(session_id=SESSION_ID, question=question, shuffle_answers=True)
    second = choice_order(session_id=SESSION_ID, question=question, shuffle_answers=True)
    assert first == second
    assert sorted(first) == list("abcd")


def test_shuffled_choice_order_differs_between_sessions(bank: QuestionBank) -> None:
    """Two learners answering the same question see independent orderings."""
    question = bank.require("clean-d01-q001")
    orders = {
        tuple(choice_order(session_id=session, question=question, shuffle_answers=True))
        for session in (SESSION_ID, OTHER_SESSION_ID)
    }
    assert len(orders) == 2


def test_presented_choices_are_relabelled_in_display_order(bank: QuestionBank) -> None:
    question = bank.require("clean-d01-q001")
    presented = present_question(
        session_id=SESSION_ID, question=question, position=1, total=5, shuffle_answers=True
    )

    assert [choice.letter for choice in presented.choices] == list(DISPLAY_LETTERS)
    assert {choice.text for choice in presented.choices} == set(question.choices.values())
    assert presented.position == 1
    assert presented.total == 5


def test_grading_recognises_the_correct_displayed_choice(bank: QuestionBank) -> None:
    question = bank.require("clean-d01-q001")
    presented = present_question(
        session_id=SESSION_ID, question=question, position=1, total=1, shuffle_answers=True
    )
    correct_letter = next(
        choice.letter for choice in presented.choices if choice.text == question.correct_choice
    )

    graded = grade_answer(
        session_id=SESSION_ID,
        question=question,
        display_choice=correct_letter,
        shuffle_answers=True,
    )
    assert graded.result is AttemptResult.correct
    assert graded.correct_display_letter == correct_letter
    assert graded.original_choice == question.answer


def test_grading_recognises_an_incorrect_choice(bank: QuestionBank) -> None:
    question = bank.require("clean-d01-q001")
    presented = present_question(
        session_id=SESSION_ID, question=question, position=1, total=1, shuffle_answers=True
    )
    wrong_letter = next(
        choice.letter for choice in presented.choices if choice.text != question.correct_choice
    )

    graded = grade_answer(
        session_id=SESSION_ID,
        question=question,
        display_choice=wrong_letter,
        shuffle_answers=True,
    )
    assert graded.result is AttemptResult.incorrect
    assert graded.original_choice != question.answer


def test_a_missing_choice_is_recorded_as_skipped(bank: QuestionBank) -> None:
    question = bank.require("clean-d01-q001")
    graded = grade_answer(
        session_id=SESSION_ID, question=question, display_choice=None, shuffle_answers=False
    )
    assert graded.result is AttemptResult.skipped
    assert graded.original_choice is None
    assert graded.correct_choice_text == question.correct_choice


def test_grading_reports_the_source_correction_when_there_is_one(bank: QuestionBank) -> None:
    question = bank.require("clean-d01-q001")
    graded = grade_answer(
        session_id=SESSION_ID, question=question, display_choice="a", shuffle_answers=False
    )
    assert graded.correction_note is None
    assert graded.explanation == question.explanation
