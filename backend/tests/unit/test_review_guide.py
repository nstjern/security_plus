"""Review guide construction."""

from __future__ import annotations

from app.core.constants import DOMAIN_NAMES
from app.models.progress import ProgressRecord
from app.models.question import Question
from app.services.question_bank import QuestionBank
from app.services.review_guide import build_review_guide


def make_question(
    question_id: str,
    *,
    subject: str,
    exam_domain: str = DOMAIN_NAMES[0],
    correct_choice: str = "Alpha",
    explanation: str = "Because alpha.",
    corrected: bool = False,
) -> Question:
    return Question(
        id=question_id,
        source_section="Domain Bank",
        grouping=exam_domain,
        exam_domain=exam_domain,
        objective="1.1 Security controls",
        subject=subject,
        question_number=1,
        question=f"Prompt for {question_id}?",
        choices={"a": correct_choice, "b": "Beta", "c": "Gamma", "d": "Delta"},
        answer="a",
        explanation=explanation,
        provenance="Original.",
        corrected=corrected,
        correction_note="Wording clarified." if corrected else "",
    )


def test_guide_is_empty_without_any_missed_questions(bank: QuestionBank) -> None:
    guide = build_review_guide(bank, {"clean-d01-q003": ProgressRecord(attempts=1, correct=1)})
    assert guide.is_empty
    assert guide.focus_areas == []
    assert guide.total_graded == 1
    assert guide.overall_accuracy == 1.0


def test_guide_reports_overall_totals(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    guide = build_review_guide(bank, records)
    assert guide.total_correct == 3
    assert guide.total_incorrect == 4
    assert guide.total_graded == 7
    assert guide.overall_accuracy == 3 / 7


def test_guide_surfaces_the_original_explanation_objective_and_chapter(
    bank: QuestionBank,
) -> None:
    question = bank.require("clean-d03-q001")
    guide = build_review_guide(bank, {question.id: ProgressRecord(attempts=1, incorrect=1)})

    concept = guide.focus_areas[0].concepts[0]
    assert concept.question_id == question.id
    assert concept.explanation == question.explanation
    assert concept.objective == question.objective
    assert concept.chapter == question.grouping
    assert concept.correct_choice == question.correct_choice
    assert concept.correction_note is None


def test_priority_domains_are_listed_in_domain_order(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    guide = build_review_guide(bank, records)
    indices = [DOMAIN_NAMES.index(domain.domain) for domain in guide.priority_domains]
    assert indices == sorted(indices)
    assert guide.priority_domains[0].domain == DOMAIN_NAMES[0]


def test_domains_answered_perfectly_are_not_prioritized(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    guide = build_review_guide(bank, records)
    assert DOMAIN_NAMES[1] not in {domain.domain for domain in guide.priority_domains}


def test_questions_teaching_the_same_concept_collapse_into_one_entry() -> None:
    synthetic = QuestionBank(
        [
            make_question("dup-1", subject="Control categories"),
            make_question("dup-2", subject="Control categories"),
        ]
    )
    missed = {
        "dup-1": ProgressRecord(attempts=1, incorrect=1),
        "dup-2": ProgressRecord(attempts=1, incorrect=1),
    }
    guide = build_review_guide(synthetic, missed)

    assert len(guide.focus_areas) == 1
    assert len(guide.focus_areas[0].concepts) == 1


def test_distinct_concepts_are_kept_separately() -> None:
    synthetic = QuestionBank(
        [
            make_question("one", subject="Control categories"),
            make_question(
                "two",
                subject="Control categories",
                correct_choice="Operational",
                explanation="Because operational.",
            ),
        ]
    )
    missed = {
        "one": ProgressRecord(attempts=1, incorrect=1),
        "two": ProgressRecord(attempts=1, incorrect=1),
    }
    guide = build_review_guide(synthetic, missed)
    assert len(guide.focus_areas[0].concepts) == 2


def test_corrected_questions_carry_their_correction_note() -> None:
    synthetic = QuestionBank([make_question("fixed", subject="Controls", corrected=True)])
    guide = build_review_guide(synthetic, {"fixed": ProgressRecord(attempts=1, incorrect=1)})
    assert guide.focus_areas[0].concepts[0].correction_note == "Wording clarified."


def test_focus_areas_can_be_capped(bank: QuestionBank, records: dict[str, ProgressRecord]) -> None:
    guide = build_review_guide(bank, records, max_focus_areas=1)
    assert len(guide.focus_areas) == 1
    assert guide.focus_areas[0].rank == 1


def test_focus_areas_are_listed_in_domain_order() -> None:
    synthetic = QuestionBank(
        [
            make_question("d4-q", subject="Ops topic", exam_domain=DOMAIN_NAMES[3]),
            make_question("d1-q", subject="General topic", exam_domain=DOMAIN_NAMES[0]),
        ]
    )
    missed = {
        # Domain 4 misses more often, but the guide should still list Domain 1 first.
        "d4-q": ProgressRecord(attempts=3, incorrect=3),
        "d1-q": ProgressRecord(attempts=1, incorrect=1),
    }
    guide = build_review_guide(synthetic, missed)

    assert [area.domain for area in guide.focus_areas] == [DOMAIN_NAMES[0], DOMAIN_NAMES[3]]
    assert [area.rank for area in guide.focus_areas] == [1, 2]


def test_records_for_unknown_questions_are_ignored() -> None:
    synthetic = QuestionBank([make_question("present", subject="Controls")])
    guide = build_review_guide(
        synthetic,
        {
            "present": ProgressRecord(attempts=1, incorrect=1),
            "absent": ProgressRecord(attempts=1, incorrect=1),
        },
    )
    assert [concept.question_id for concept in guide.focus_areas[0].concepts] == ["present"]
