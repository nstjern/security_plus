# Security+ Study API

FastAPI service behind the Security+ study application. It owns the question bank, grades
answers, tracks progress per learner, and builds the personalized review guide.

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
  core/              Settings, logging, security headers, hashing, rate limiting
  models/            Domain models: questions, progress, review guide
  services/          Question bank, statistics, review guide, session rules
  repositories/      Database reads and writes, one module per aggregate
  db/                SQLModel tables and session management
  api/               Routes, schemas, dependencies, cookie handling
  export_openapi.py  Writes contracts/openapi.json
alembic/             Migrations
tests/unit/          Domain logic, services, and repositories
tests/api/           HTTP behaviour, including auth and response hardening
```

Routes depend on services and repositories; services never import repositories, so the rules
about how a session behaves stay testable without a database.

## Current endpoints

Public:

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness; never touches the database |
| GET | `/readyz` | Readiness; reports 503 when the database is unreachable |
| GET | `/api/catalog` | Every domain, chapter, subject, and objective |
| GET | `/api/questions` | Browse questions, filtered and paginated |
| GET | `/api/questions/{id}` | One question |

Authentication:

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Create an account and sign in |
| POST | `/api/auth/login` | Sign in; rate limited |
| POST | `/api/auth/logout` | Revoke the session |
| GET | `/api/auth/me` | The signed-in user |

Signed in:

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/sessions` | Start a study session |
| GET | `/api/sessions` | Recent sessions |
| GET | `/api/sessions/{id}` | Read a session |
| GET | `/api/sessions/{id}/current-question` | The question awaiting an answer |
| POST | `/api/sessions/{id}/answer` | Submit an answer, receive the explanation |
| POST | `/api/sessions/{id}/end` | End a session early |
| GET | `/api/sessions/{id}/summary` | How the session went |
| GET | `/api/progress/summary` | Accuracy by domain |
| GET | `/api/progress/subjects` | Weakest subjects |
| GET | `/api/progress/missed` | Questions missed at least once |
| GET | `/api/review-guide` | Weak areas and the concepts behind each miss |

Answers and explanations never appear in a browsing or current-question response. Grading
happens server-side, and the key is returned only in the reply to a submitted answer.

## Calling it from a browser

Authentication uses cookies, not a bearer token, so requests need `credentials: 'include'`.
State-changing requests must echo the CSRF cookie in an `X-CSRF-Token` header:

```js
await fetch("http://localhost:8000/api/sessions", {
  method: "POST",
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
    "X-CSRF-Token": readCookie("sp_csrf"),
  },
  body: JSON.stringify({ mode: "practice", count: 20 }),
});
```

Study modes are `all`, `domain`, `chapter`, `subject`, `objective`, `missed`, and `practice`.
The filtered modes need a `filter_value`; `practice` takes a `count`.
