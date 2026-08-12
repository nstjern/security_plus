"""Aggregation and weak-area ranking."""

from __future__ import annotations

from app.core.constants import DOMAIN_NAMES
from app.models.progress import ProgressRecord
from app.services.question_bank import QuestionBank
from app.services.statistics import (
    calculate_weak_areas,
    group_results,
    lowest_performing_subjects,
)


def test_group_results_totals_by_domain(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    grouped = group_results(bank, records, field="domain")
    first_domain = grouped[DOMAIN_NAMES[0]]
    assert first_domain.attempts == 5
    assert first_domain.correct == 1
    assert first_domain.incorrect == 4
    assert first_domain.graded == 5


def test_group_results_ignores_unknown_question_ids(bank: QuestionBank) -> None:
    grouped = group_results(bank, {"not-a-question": ProgressRecord(attempts=9)}, field="domain")
    assert grouped == {}


def test_group_results_can_group_by_objective(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    grouped = group_results(bank, records, field="objective")
    assert grouped
    assert all(stats.attempts > 0 for stats in grouped.values())


def test_weak_areas_rank_repeated_misses_above_isolated_ones(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    areas = calculate_weak_areas(bank, records)
    assert len(areas) == 2
    assert areas[0].incorrect == 3
    assert areas[0].accuracy == 0.25
    assert areas[0].weakness_score > areas[1].weakness_score


def test_weak_areas_exclude_subjects_answered_correctly(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    correct_only_subject = bank.require("clean-d02-q002").subject
    subjects = {area.subject for area in calculate_weak_areas(bank, records)}
    assert correct_only_subject not in subjects


def test_weak_areas_collect_the_missed_question_ids(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    areas = calculate_weak_areas(bank, records)
    assert areas[0].missed_question_ids == ["clean-d01-q003"]


def test_lowest_performing_subjects_orders_by_accuracy(
    bank: QuestionBank, records: dict[str, ProgressRecord]
) -> None:
    subjects = lowest_performing_subjects(bank, records, limit=2)
    assert len(subjects) == 2
    assert subjects[0].accuracy <= subjects[1].accuracy


def test_stats_with_no_graded_attempts_report_zero_accuracy(bank: QuestionBank) -> None:
    skipped_only = {"clean-d01-q003": ProgressRecord(attempts=1, skipped=1)}
    grouped = group_results(bank, skipped_only, field="domain")
    stats = grouped[DOMAIN_NAMES[0]]
    assert stats.graded == 0
    assert stats.accuracy == 0.0
    assert stats.error_rate == 0.0
    assert calculate_weak_areas(bank, skipped_only) == []
