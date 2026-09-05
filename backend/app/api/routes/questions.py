"""Read-only access to the question bank."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_question_bank
from app.api.schemas import QuestionPage, QuestionSummary
from app.services.question_bank import QuestionBank

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=QuestionPage, summary="Browse questions")
def list_questions(
    bank: QuestionBank = Depends(get_question_bank),
    domain: str | None = Query(default=None),
    chapter: str | None = Query(default=None),
    subject: str | None = Query(default=None),
    objective: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> QuestionPage:
    matches = bank.filter(domain=domain, chapter=chapter, subject=subject, objective=objective)
    window = matches[offset : offset + limit]
    return QuestionPage(
        items=[QuestionSummary.from_question(question) for question in window],
        total=len(matches),
        limit=limit,
        offset=offset,
    )


@router.get("/{question_id}", response_model=QuestionSummary, summary="Read one question")
def read_question(
    question_id: str,
    bank: QuestionBank = Depends(get_question_bank),
) -> QuestionSummary:
    question = bank.get(question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return QuestionSummary.from_question(question)
