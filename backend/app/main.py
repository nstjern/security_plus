"""Application factory and entry point."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import catalog, health, questions
from app.core.config import Settings, get_settings
from app.core.constants import API_VERSION
from app.core.logging import configure_logging
from app.core.middleware import SecurityHeadersMiddleware
from app.services.question_bank import QuestionBank

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load and validate the question bank once, failing fast if it is malformed."""
    settings = get_settings()
    bank = QuestionBank.from_file(settings.questions_path)
    app.state.question_bank = bank
    logger.info(
        "question bank loaded",
        extra={"question_count": len(bank), "path": str(settings.questions_path)},
    )
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Security+ Study API",
        version=API_VERSION,
        summary="Study sessions, progress tracking, and personalized review guides.",
        lifespan=lifespan,
        # Interactive docs are a development convenience, not a production endpoint.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
    )

    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=settings.is_production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )

    app.include_router(health.router)
    app.include_router(catalog.router, prefix="/api")
    app.include_router(questions.router, prefix="/api")
    return app


app = create_app()
