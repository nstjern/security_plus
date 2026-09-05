# Security+ Study

A full-stack study application for the CompTIA Security+ SY0-701 exam objectives, built
around 136 independently authored practice questions. It grades answers server-side, tracks
accuracy per domain and subject, and turns the questions a learner missed into a personalized
review guide.

This project is not affiliated with or endorsed by CompTIA. Its questions are original study
material, not official exam items.

## Run it

With Docker installed:

```bash
docker compose up --build
docker compose exec api alembic upgrade head
```

| What | Where |
|---|---|
| Study app | http://localhost:5173 |
| API documentation | http://localhost:8000/docs |

Create an account on first visit; progress is stored against it.

## Layout

| Path | What it is |
|---|---|
| `frontend/` | React and TypeScript interface — see [frontend/README.md](frontend/README.md) |
| `backend/` | FastAPI service — see [backend/README.md](backend/README.md) |
| `questions.json` | The question bank, loaded and validated at API startup |
| `contracts/` | The generated OpenAPI document and architecture decision records |
| `SECURITY.md` | The security controls, mapped to SY0-701 domains |

## How it fits together

The browser talks to the API across origins with a session cookie, so the interesting parts of
the exam material are also the parts holding the application up: `HttpOnly` cookies, CSRF
tokens, CORS, password hashing, rate limiting, and authorization on every query.

`contracts/openapi.json` is the boundary between the two halves. The backend generates it, the
frontend generates its TypeScript types from it, and CI fails if either drifts from what is
committed.

## Study modes

Sessions can cover everything, a single exam domain, a chapter, a subject, an objective, a
random practice quiz of a chosen size, or missed questions. For missed mode you can revisit
every question you have ever gotten wrong, or limit the session to questions you have not
answered correctly yet. Answer choices can be shuffled so a remembered letter is not mistaken
for a remembered concept. Every answer is graded by the API, which is also the only place the
correct answer and its explanation exist.

## Review guide

Weak areas are ranked using both how many questions were missed and the rate at which they
were missed, so two wrong out of two outranks two wrong out of ten. Each focus area carries
the concept behind each missed question, its explanation, and the objective and chapter to go
back to. The dashboard links straight into a filtered view by domain or weak subject; the
review guide itself can also be filtered by domain from the page.

## Development

Both halves are checked the same way in CI: linting, formatting, type checking, tests with
coverage thresholds, a container build that must run as a non-root user, and drift checks on
the API contract and the database migrations.

```bash
cd backend && pytest && ruff check . && mypy app
cd frontend && npm test && npm run lint && npm run typecheck
```
