"""Aggregation and weak-area ranking.

Ported from the CLI's ``group_results`` and ``calculate_weak_areas`` so the web app and the
terminal program rank weaknesses identically.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from app.models.progress import GroupStats, ProgressRecord, WeakArea
from app.services.question_bank import QuestionBank

GroupField = Literal["domain", "subject", "grouping", "objective"]


def group_results(
    bank: QuestionBank,
    records: Mapping[str, ProgressRecord],
    *,
    field: GroupField,
) -> dict[str, GroupStats]:
    """Total attempts by domain, subject, chapter, or objective."""
    grouped: dict[str, GroupStats] = {}
    for question_id, record in records.items():
        question = bank.get(question_id)
        if question is None:
            continue
        name = str(getattr(question, field))
        stats = grouped.setdefault(name, GroupStats(name=name))
        stats.attempts += record.attempts
        stats.correct += record.correct
        stats.incorrect += record.incorrect
        stats.skipped += record.skipped
    return grouped


def calculate_weak_areas(
    bank: QuestionBank,
    records: Mapping[str, ProgressRecord],
) -> list[WeakArea]:
    """Rank domain-and-subject pairs the learner has missed, strongest weakness first."""
    grouped: dict[tuple[str, str], WeakArea] = {}
    for question_id, record in records.items():
        question = bank.get(question_id)
        if question is None:
            continue

        key = (question.domain, question.subject)
        area = grouped.setdefault(key, WeakArea(domain=key[0], subject=key[1]))
        area.attempts += record.attempts
        area.correct += record.correct
        area.incorrect += record.incorrect
        area.skipped += record.skipped
        if record.incorrect > 0:
            area.missed_question_ids.append(question_id)

    weak_areas = [area for area in grouped.values() if area.incorrect > 0]
    weak_areas.sort(
        key=lambda area: (
            -area.weakness_score,
            area.accuracy,
            -area.graded,
            area.domain,
            area.subject,
        )
    )
    return weak_areas


def lowest_performing_subjects(
    bank: QuestionBank,
    records: Mapping[str, ProgressRecord],
    *,
    limit: int = 10,
) -> list[GroupStats]:
    """Subjects with at least one graded attempt, least accurate first."""
    attempted = [
        stats for stats in group_results(bank, records, field="subject").values() if stats.graded
    ]
    attempted.sort(key=lambda stats: (stats.accuracy, -stats.graded, stats.name))
    return attempted[:limit]
