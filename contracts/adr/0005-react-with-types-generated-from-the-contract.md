# 5. React and TypeScript, with API types generated from the contract

- Status: Accepted
- Date: 2026-08-12

## Context

The backend already publishes an OpenAPI document that CI checks for drift. The frontend
needs to consume that API without the usual failure mode, where a renamed field is only
discovered when a page renders `undefined` in front of a user.

The realistic options were a framework with server-side rendering (Next.js, Remix), a plain
single-page application, or server-rendered templates from FastAPI itself.

## Decision

Build a single-page application with React, TypeScript, and Vite, and generate the API types
from `contracts/openapi.json` with `openapi-typescript`. Calls go through `openapi-fetch`, so
paths, query parameters, request bodies, and responses are all checked against the contract at
compile time.

Server state lives in TanStack Query rather than in hand-written effects and reducers, since
almost everything on screen is a cached view of an API response.

## Consequences

- Renaming a field in the backend breaks the frontend build rather than a page at runtime, and
  a dedicated CI job fails if the checked-in types drift from the checked-in contract.
- There is no server-side rendering. For an authenticated study tool with no public content to
  index, the SEO and first-paint arguments for it do not apply, and it would have added a Node
  runtime to operate in production. The frontend ships as static files behind nginx instead.
- The API and the frontend are separate origins, which forces the CORS and cookie questions to
  be answered explicitly rather than avoided by same-origin convenience. See ADR 0004.
- TypeScript is pinned to 5.x: `openapi-typescript` does not yet support 6.x.
