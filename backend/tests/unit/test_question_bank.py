"""Question bank loading, validation, and querying."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.constants import DOMAIN_NAMES
from app.models.question import Question, chapter_sort_key
from app.services.question_bank import QuestionBank, QuestionBankError

EXPECTED_QUESTION_COUNT = 136

EXPECTED_DOMAIN_COUNTS = {
    DOMAIN_NAMES[0]: 16,
    DOMAIN_NAMES[1]: 30,
    DOMAIN_NAMES[2]: 24,
    DOMAIN_NAMES[3]: 38,
    DOMAIN_NAMES[4]: 28,
}


def test_bank_loads_expected_question_count(bank: QuestionBank) -> None:
    assert len(bank) == EXPECTED_QUESTION_COUNT


def test_question_ids_are_unique(bank: QuestionBank) -> None:
    ids = [question.id for question in bank]
    assert len(ids) == len(set(ids))


def test_every_question_offers_four_choices_and_a_valid_answer(bank: QuestionBank) -> None:
    for question in bank:
        assert set(question.choices) == set("abcd"), question.id
        assert question.answer in question.choices, question.id


def test_every_question_declares_original_provenance(bank: QuestionBank) -> None:
    for question in bank:
        assert question.id.startswith("clean-")
        assert question.provenance == (
            "Original question authored for this project; not an official CompTIA item."
        )
        assert not question.corrected
        assert question.correction_note == ""


def test_domain_counts_match_the_published_bank(bank: QuestionBank) -> None:
    counts = {
        domain: sum(question.exam_domain == domain for question in bank) for domain in DOMAIN_NAMES
    }
    assert counts == EXPECTED_DOMAIN_COUNTS


def test_chapters_cover_one_through_seventeen(bank: QuestionBank) -> None:
    chapters = bank.chapters()
    assert [chapter_sort_key(chapter)[0] for chapter in chapters] == list(range(1, 18))


def test_domain_resolves_from_explicit_field_and_chapter_fallback(bank: QuestionBank) -> None:
    assert bank.require("clean-d04-q033").domain == DOMAIN_NAMES[3]
    assert bank.require("clean-d02-q002").domain == DOMAIN_NAMES[1]


def test_chapter_fallback_applies_when_exam_domain_is_absent() -> None:
    question = Question(
        id="local-1",
        source_section="Chapter Quizzes",
        grouping="Chapter 7: Architecture",
        objective="3.1",
        subject="Zones",
        question_number=1,
        question="Which zone?",
        choices={"a": "One", "b": "Two", "c": "Three", "d": "Four"},
        answer="a",
        explanation="Because.",
        provenance="Original.",
    )
    assert question.domain == DOMAIN_NAMES[2]
    assert question.chapter_number == 7
    assert question.short_domain == "Domain 3"


def test_unparseable_chapter_labels_are_reported_as_unmapped() -> None:
    question = Question(
        id="local-2",
        source_section="Chapter Quizzes",
        grouping="Chapter unknown",
        objective="3.1",
        subject="Zones",
        question_number=1,
        question="Which zone?",
        choices={"a": "One", "b": "Two", "c": "Three", "d": "Four"},
        answer="a",
        explanation="Because.",
        provenance="Original.",
    )
    assert question.chapter_number is None
    assert question.domain == "Unmapped chapter questions"


def test_answer_must_identify_one_of_the_choices() -> None:
    with pytest.raises(ValueError, match="is not one of its choices"):
        Question(
            id="local-3",
            source_section="Domain Bank",
            grouping="Domain 1: General Security Concepts",
            objective="1.1",
            subject="Controls",
            question_number=1,
            question="Which control?",
            choices={"a": "One", "b": "Two"},
            answer="d",
            explanation="Because.",
            provenance="Original.",
        )


def test_filtering_narrows_by_domain_and_subject(bank: QuestionBank) -> None:
    subject = bank.require("clean-d01-q003").subject
    matches = bank.filter(domain=DOMAIN_NAMES[0], subject=subject)
    assert matches
    assert all(q.domain == DOMAIN_NAMES[0] and q.subject == subject for q in matches)


def test_filtering_by_question_ids_returns_only_those_questions(bank: QuestionBank) -> None:
    wanted = {"clean-d01-q003", "clean-d01-q004"}
    assert {question.id for question in bank.filter(question_ids=wanted)} == wanted


def test_missing_question_lookup_behaviour(bank: QuestionBank) -> None:
    assert bank.get("does-not-exist") is None
    with pytest.raises(KeyError):
        bank.require("does-not-exist")


def test_duplicate_ids_are_rejected(bank: QuestionBank) -> None:
    duplicated = [bank.questions[0], bank.questions[0]]
    with pytest.raises(QuestionBankError, match="Duplicate question ID"):
        QuestionBank(duplicated)


def test_empty_bank_is_rejected() -> None:
    with pytest.raises(QuestionBankError, match="at least one question"):
        QuestionBank([])


def test_missing_file_raises_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(QuestionBankError, match="not found"):
        QuestionBank.from_file(tmp_path / "absent.json")


def test_invalid_json_raises_a_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "questions.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(QuestionBankError, match="not valid JSON"):
        QuestionBank.from_file(path)


def test_non_list_payload_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps({"id": "x"}), encoding="utf-8")
    with pytest.raises(QuestionBankError, match="must be a JSON list"):
        QuestionBank.from_file(path)


def test_malformed_entries_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps([{"id": "x"}]), encoding="utf-8")
    with pytest.raises(QuestionBankError, match="failed validation"):
        QuestionBank.from_file(path)
