# Security+ Study Web App

React interface for the Security+ study API. It signs learners in, runs study sessions, and
renders the personalized review guide the API builds from missed questions.

## Run it

The API has to be running first. From the repository root:

```bash
docker compose up --build
```

That serves the built frontend at http://localhost:5173 and the API at http://localhost:8000.

For frontend work with hot reload, run the backend only and start Vite locally:

```bash
docker compose up db api
cd frontend
npm install
npm run dev
```

`VITE_API_URL` selects the API origin and defaults to `http://localhost:8000`. Whatever you
choose must also appear in the API's `CORS_ORIGINS`, because the browser will not send the
session cookie cross-origin otherwise.

## Scripts

| Command                           | What it does                                                      |
| --------------------------------- | ----------------------------------------------------------------- |
| `npm run dev`                     | Vite dev server on port 5173                                      |
| `npm run build`                   | Type check, then produce `dist/`                                  |
| `npm run typecheck`               | TypeScript only                                                   |
| `npm run lint`                    | oxlint, including the react and jsx-a11y rules                    |
| `npm run format` / `format:check` | Prettier                                                          |
| `npm test`                        | Vitest, jsdom, MSW-backed                                         |
| `npm run test -- --coverage`      | Same with a coverage report and 80% thresholds                    |
| `npm run api:types`               | Regenerate `src/api/schema.d.ts` from `../contracts/openapi.json` |

## How it talks to the API

The API contract is the source of truth. `openapi-typescript` turns
`contracts/openapi.json` into `src/api/schema.d.ts`, and `openapi-fetch` uses those types to
check every path, query parameter, and request body at compile time. Change an endpoint in
the backend, regenerate, and anything stale stops compiling. CI fails if the committed types
no longer match the committed contract.

Authentication rides on two cookies:

- `sp_session` is `HttpOnly`, so JavaScript cannot read it and neither can an injected script.
  The browser sends it automatically because every request sets `credentials: 'include'`.
- `sp_csrf` is deliberately readable. A middleware in `src/api/client.ts` copies it into the
  `X-CSRF-Token` header on every unsafe request, which is the half of the double-submit pair
  a cross-site attacker cannot forge.

Nothing about the session is kept in `localStorage`, so there is no token for a cross-site
scripting bug to steal.

## Layout

```
src/api/         Generated schema, typed client, query hooks, error translation
src/auth/        Auth context and the route guard
src/components/  Buttons, cards, fields, feedback states, page shell
src/pages/       One file per screen, each with a sibling test
src/test/        MSW handlers, fixtures, and a render helper
```

## Screens

| Route           | What it does                                                                                                                                                                                |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/`             | Dashboard — progress stats, accuracy by domain, weakest subjects, and a shortcut to practise missed questions. Domain and subject rows link into the review guide with that filter applied. |
| `/study`        | Start a session — choose a study mode, including missed questions with either all ever-missed or only not-yet-correct scope.                                                                |
| `/sessions/:id` | Answer questions — keyboard shortcuts: `a`–`d` to select, Enter to submit, Enter again to advance.                                                                                        |
| `/review-guide` | Review guide — weak areas ranked by domain, filterable by domain or subject via the page or URL query (`?domain=…`, `?subject=…`).                                                          |

## Tests

Tests drive the real application through `renderApp()`, with
[MSW](https://mswjs.io) answering as the API. That means routing, the auth guard, the query
cache, and error handling all take part rather than being mocked away. Unhandled requests
fail the suite, so a test cannot accidentally depend on a live backend.
