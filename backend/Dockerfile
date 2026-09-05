# syntax=docker/dockerfile:1
#
# Build context is the repository root so questions.json can be copied in.
#   docker build -f backend/Dockerfile .

FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Dependencies are installed before the source is copied so the layer caches.
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir .


FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    QUESTIONS_PATH=/srv/questions.json

# The application runs as an unprivileged user; nothing here needs root.
RUN groupadd --system appuser && useradd --system --gid appuser --home-dir /app appuser

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY questions.json /srv/questions.json

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
