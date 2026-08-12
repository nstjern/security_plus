"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import Request

from app.services.question_bank import QuestionBank


def get_question_bank(request: Request) -> QuestionBank:
    """Return the bank loaded once during application startup."""
    bank: QuestionBank = request.app.state.question_bank
    return bank
