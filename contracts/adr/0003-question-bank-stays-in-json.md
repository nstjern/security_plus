# 3. The question bank stays in version-controlled JSON

- Status: Accepted
- Date: 2026-08-12

## Context

`questions.json` holds 136 original questions. Moving them into Postgres would allow
full-text search, an admin editing interface, and per-user banks.

None of those features exist or are planned for the current phase.

## Decision

Keep the question bank in JSON, loaded and validated once at application startup. The database
stores learner-owned data only: accounts, progress, sessions, and answers.

## Consequences

- Question changes are reviewed as diffs in pull requests, which suits authored study content.
- A malformed bank fails at startup with a precise validation error rather than at request time.
- Progress rows reference questions by string ID with no foreign key, so a deleted question
  leaves an orphaned progress row. Services already ignore records whose question is absent.
- Adding an admin editing interface later means introducing a `questions` table and a seeding
  path. That work is deliberately deferred until the feature is real.
