# Security+ Study API

FastAPI service behind the Security+ study application. The domain logic — question bank
validation, weak-area ranking, review guide construction — is ported from the original
terminal program (`../quiz.py`), so both interfaces rank weaknesses identically.

## Run it

From the repository root, with Docker installed:

```bash
docker compose up --build
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Liveness: http://localhost:8000/healthz
- Readiness (includes the database): http://localhost:8000/readyz

`compose.override.yml` is merged automatically and adds the source mount, auto-reload, and a
published database port. A deployment would use `docker compose -f compose.yml` to skip it.

Stop with `docker compose down`, or `docker compose down -v` to discard the database volume.

## Work on it without Docker

```bash
cd backend
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev]"
```

The database still comes from Compose:

```bash
docker compose up -d db
export DATABASE_URL="postgresql+psycopg://app:app@localhost:5432/app"
./.venv/bin/alembic upgrade head
./.venv/bin/uvicorn app.main:app --reload
```

## Checks

Everything below also runs in CI on every pull request.

```bash
./.venv/bin/ruff check .          # lint
./.venv/bin/ruff format --check . # formatting
./.venv/bin/mypy app              # strict type checking
./.venv/bin/pytest                # tests, with an 85% coverage floor
```

Install the pre-commit hooks once so formatting never fails a pull request:

```bash
./.venv/bin/pre-commit install
```

## Database changes

The schema is managed only by Alembic; nothing calls `create_all`.

```bash
./.venv/bin/alembic revision --autogenerate -m "what changed"
./.venv/bin/alembic upgrade head
./.venv/bin/alembic check          # fails when models and migrations disagree
```

CI runs all three, plus `alembic downgrade base`, so a migration without a working reverse
path fails the build.

## The API contract

`../contracts/openapi.json` is generated, committed, and checked for drift in CI:

```bash
./.venv/bin/python -m app.export_openapi
```

Once the frontend exists, its TypeScript types are generated from that same file.

## Layout

```
app/
  main.py            Application factory, middleware, router wiring
  core/              Settings, logging, security headers, exam taxonomy
  models/            Domain models: questions, progress, review guide
  services/          Question bank, statistics, review guide construction
  db/                SQLModel tables and session management
  api/               Routes, request/response schemas, dependencies
  export_openapi.py  Writes contracts/openapi.json
alembic/             Migrations
tests/unit/          Domain logic, ported from ../test_quiz.py
tests/api/           HTTP behaviour, including response hardening
```

## Current endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness; never touches the database |
| GET | `/readyz` | Readiness; reports 503 when the database is unreachable |
| GET | `/api/catalog` | Every domain, chapter, subject, and objective |
| GET | `/api/questions` | Browse questions, filtered and paginated |
| GET | `/api/questions/{id}` | One question |

Answers and explanations are deliberately absent from every response above. They are revealed
only in the reply to a submitted answer, which arrives with study sessions in the next phase.
