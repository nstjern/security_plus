"""Building the personalized review guide.

Missed questions are grouped by subject, ranked by weakness score, and turned into concepts
carrying the explanation, objective, and chapter a learner needs to study the topic again.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from app.models.progress import ProgressRecord
from app.models.review import DomainPriority, FocusArea, ReviewConcept, ReviewGuide
from app.services.question_bank import QuestionBank
from app.services.statistics import calculate_weak_areas, group_results


def _priority_domains(
    bank: QuestionBank,
    records: Mapping[str, ProgressRecord],
) -> list[DomainPriority]:
    scored = []
    for stats in group_results(bank, records, field="domain").values():
        if not stats.graded or not stats.incorrect:
            continue
        scored.append((stats.incorrect * stats.error_rate, stats))
    scored.sort(key=lambda item: (-item[0], item[1].name))

    return [
        DomainPriority(
            rank=rank,
            domain=stats.name,
            accuracy=stats.accuracy,
            incorrect=stats.incorrect,
            weakness_score=score,
        )
        for rank, (score, stats) in enumerate(scored, start=1)
    ]


def _concepts(bank: QuestionBank, missed_question_ids: list[str]) -> list[ReviewConcept]:
    """Collapse missed questions that teach the same concept into a single entry."""
    concepts: list[ReviewConcept] = []
    seen: set[tuple[str, str]] = set()
    for question_id in missed_question_ids:
        question = bank.get(question_id)
        if question is None:
            continue
        signature = (question.correct_choice, question.explanation.strip())
        if signature in seen:
            continue
        seen.add(signature)
        concepts.append(
            ReviewConcept(
                question_id=question.id,
                objective=question.objective,
                chapter=question.grouping,
                prompt=question.question,
                correct_choice=question.correct_choice,
                explanation=question.explanation,
                correction_note=question.correction_note if question.corrected else None,
            )
        )
    return concepts


def build_review_guide(
    bank: QuestionBank,
    records: Mapping[str, ProgressRecord],
    *,
    max_focus_areas: int | None = None,
    generated_at: datetime | None = None,
) -> ReviewGuide:
    """Rank weak areas and gather the concepts behind each missed question."""
    weak_areas = calculate_weak_areas(bank, records)
    if max_focus_areas is not None:
        weak_areas = weak_areas[:max_focus_areas]

    domain_stats = group_results(bank, records, field="domain").values()
    total_correct = sum(stats.correct for stats in domain_stats)
    total_incorrect = sum(stats.incorrect for stats in domain_stats)
    total_graded = total_correct + total_incorrect

    focus_areas = [
        FocusArea(
            rank=rank,
            domain=area.domain,
            subject=area.subject,
            accuracy=area.accuracy,
            correct=area.correct,
            incorrect=area.incorrect,
            weakness_score=area.weakness_score,
            concepts=_concepts(bank, area.missed_question_ids),
        )
        for rank, area in enumerate(weak_areas, start=1)
    ]

    return ReviewGuide(
        generated_at=generated_at or datetime.now(UTC),
        total_graded=total_graded,
        total_correct=total_correct,
        total_incorrect=total_incorrect,
        overall_accuracy=total_correct / total_graded if total_graded else 0.0,
        priority_domains=_priority_domains(bank, records),
        focus_areas=focus_areas,
    )
