"""The personalized review guide."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import Bank, CurrentUser, DbSession, require_user_id
from app.models.review import ReviewGuide
from app.repositories import progress as progress_repository
from app.services.review_guide import build_review_guide

router = APIRouter(prefix="/review-guide", tags=["review"])


@router.get(
    "",
    response_model=ReviewGuide,
    summary="Weak areas and the concepts behind every missed question",
)
def read_review_guide(
    user: CurrentUser,
    db: DbSession,
    bank: Bank,
    max_focus_areas: int | None = Query(default=None, ge=1, le=50),
) -> ReviewGuide:
    """Empty focus areas mean nothing has been answered incorrectly yet."""
    records = progress_repository.load_records(db, require_user_id(user))
    return build_review_guide(bank, records, max_focus_areas=max_focus_areas)
