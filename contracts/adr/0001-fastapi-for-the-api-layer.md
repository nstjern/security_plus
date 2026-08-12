# 1. FastAPI for the API layer

- Status: Accepted
- Date: 2026-08-12

## Context

The application began as a terminal program (`quiz.py`) whose domain logic — question bank
validation, weak-area ranking, review guide construction — was already sound and tested. The
web version needs an HTTP layer around that logic, and a typed contract the frontend can
consume.

A Flask application, matching the course template, was the obvious alternative.

## Decision

Use FastAPI.

## Consequences

- Request and response validation is declarative through Pydantic, replacing hand-written
  checks with schema definitions.
- An OpenAPI document is generated from the code, so `contracts/openapi.json` cannot drift
  from the implementation without CI noticing.
- Dependency injection gives request-scoped database sessions without global state.
- The cost is unfamiliarity relative to Flask, and async semantics that this application does
  not yet need. Routes are defined synchronously until a measured reason to change appears.
