# 2. Postgres from the start, with Alembic migrations

- Status: Accepted
- Date: 2026-08-12

## Context

SQLite would have been simpler for a single-user study application, and the schema could have
been created at startup with `SQLModel.metadata.create_all()` as the course template does.

Both shortcuts have a known end date. Progress data is per-user, so a real database is needed
as soon as accounts exist, and `create_all` cannot express a change to an existing table.

## Decision

Run Postgres in Docker for every environment, and manage the schema exclusively with Alembic.

## Consequences

- Development, CI, and any deployment exercise the same database engine, so dialect
  differences cannot hide until deployment.
- Every schema change is a reviewable file with an upgrade and a downgrade path.
- CI runs `alembic upgrade head`, then `alembic check` to fail the build when models and
  migrations disagree, then `alembic downgrade base` to prove the reverse path works.
- The cost is that contributors need Docker running to work on anything touching the database.
