"""Filter values a client needs to build a study session."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_question_bank
from app.api.schemas import CatalogResponse
from app.services.question_bank import QuestionBank

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=CatalogResponse, summary="List every available filter value")
def read_catalog(bank: QuestionBank = Depends(get_question_bank)) -> CatalogResponse:
    return CatalogResponse(
        domains=bank.domains(),
        chapters=bank.chapters(),
        subjects=bank.subjects(),
        objectives=bank.objectives(),
        question_count=len(bank),
    )
