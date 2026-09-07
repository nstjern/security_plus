# Security posture

This application teaches CompTIA Security+ material, so it holds itself to the practices it
describes. Each control below is mapped to the SY0-701 domain it belongs to.

Controls marked **planned** are recorded decisions, not implemented behaviour. They are listed
so the gap between the current state and the target state stays visible.

## Application

| Control | Status | SY0-701 domain |
|---|---|---|
| Answers and explanations are never returned by browsing endpoints | Implemented | 3.0 Security Architecture |
| Answers graded server-side; the key is sent only after the learner commits | Implemented | 3.0 Security Architecture |
| Request and response validation on every endpoint via Pydantic schemas | Implemented | 2.0 Threats and Mitigations |
| Parameterized queries only; no string-built SQL | Implemented | 2.0 Threats and Mitigations |
| Interactive API documentation disabled in production | Implemented | 3.0 Security Architecture |
| Argon2id password hashing, with transparent rehash when cost parameters change | Implemented | 1.0 General Security Concepts |
| `HttpOnly`, `Secure`, `SameSite=Lax` session cookies rather than tokens in browser storage | Implemented | 1.0 General Security Concepts |
| Sessions revocable server-side, so sign-out invalidates a captured cookie | Implemented | 1.0 General Security Concepts |
| Session tokens stored only as keyed digests, peppered with `SECRET_KEY` | Implemented | 3.0 Security Architecture |
| Double-submit CSRF tokens, validated against the server-side session | Implemented | 2.0 Threats and Mitigations |
| Rate limiting on sign-in, with `Retry-After` | Implemented | 4.0 Security Operations |
| Uniform failure message and equalized timing on sign-in | Implemented | 2.0 Threats and Mitigations |
| Every session and progress query scoped to the owning user | Implemented | 3.0 Security Architecture |
| Account lockout after sustained failures | Planned | 4.0 Security Operations |
| Password breach-list screening | Planned | 1.0 General Security Concepts |

The session cookie decision and its trade-offs are recorded in
[ADR 0004](contracts/adr/0004-session-cookies-instead-of-jwt-in-storage.md).

### Notes on specific choices

**Password length over composition.** Registration requires 12 characters and imposes no
character-class rules. Complexity requirements push people toward predictable substitutions
without adding meaningful entropy.

**Two tokens, two purposes.** The session cookie is `HttpOnly` so injected script cannot read
it. The CSRF cookie is deliberately readable, because the frontend has to echo it in a header;
its value alone proves nothing, since the server compares it against the session record rather
than against the cookie.

**User enumeration.** A wrong password and an unknown username return the same status and the
same message. When the username does not exist, the server still verifies against a throwaway
hash so the response takes comparable time.

**Rate limiting scope.** Counters live in the worker process, so the effective limit scales
with worker count. That is adequate for slowing credential stuffing here and inadequate for
anything larger; moving the counters to Postgres or Redis is the upgrade path.

**Answer shuffling.** Choice order is derived from the session and question identifiers with a
non-cryptographic generator. Presentation order is a usability concern, not a secret: the
answer key is never sent before the learner commits.

## Browser client

| Control | Status | SY0-701 domain |
|---|---|---|
| No credential in `localStorage` or `sessionStorage`; the session lives in an `HttpOnly` cookie | Implemented | 1.0 General Security Concepts |
| CSRF token attached to every unsafe request, and only to unsafe requests | Implemented | 2.0 Threats and Mitigations |
| Answers and explanations reach the browser only after an answer is submitted | Implemented | 3.0 Security Architecture |
| Cached progress dropped when a learner signs out, so a shared machine leaks nothing | Implemented | 4.0 Security Operations |
| Content-Security-Policy on the static site, allowing calls only to the configured API origin | Implemented | 3.0 Security Architecture |
| React escapes interpolated content; no use of `dangerouslySetInnerHTML` | Implemented | 2.0 Threats and Mitigations |

The frontend never decides whether an answer was right. It renders what the API graded, and
the API is the only place the answer key exists.

## Response headers

The static site is served by nginx with its own policy, which permits `connect-src` to the API
origin and nothing else. The headers below are set by `SecurityHeadersMiddleware` on every API
response:

| Header | Value | Why |
|---|---|---|
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'; base-uri 'none'` | A JSON API never needs to load or embed anything |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type confusion attacks |
| `X-Frame-Options` | `DENY` | Blocks clickjacking |
| `Referrer-Policy` | `no-referrer` | Keeps URLs out of third-party logs |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isolates the browsing context |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Production only, where TLS terminates |

Documentation routes are exempt from the strict content policy because Swagger UI loads
scripts from a CDN. No other route is exempt.

## Configuration and secrets

- Settings are typed and validated at startup by `pydantic-settings`.
- The application **refuses to start** in production while `SECRET_KEY` still matches the
  development default. A misconfiguration fails loudly instead of running insecurely.
- `SECRET_KEY` is held as a `SecretStr`, so it does not appear in logs or tracebacks.
- `.env` is gitignored; `.env.example` documents each variable and contains no real values.
- CORS lists explicit origins, because credentialed requests are incompatible with wildcards.

## Container and supply chain

| Control | Status |
|---|---|
| Both images run as an unprivileged user (`appuser` for the API, uid 101 for nginx) | Implemented |
| Multi-stage builds; no compilers, Node runtime, or build tooling in either runtime image | Implemented |
| CI asserts neither image runs as root | Implemented |
| `pip-audit` and `npm audit` fail the build on known vulnerable dependencies | Implemented |
| Dependencies pinned to compatible ranges | Implemented |
| Container image scanning (Trivy) | Planned |
| Static analysis (CodeQL) and secret scanning (Gitleaks) | Planned |
| Dependabot update automation | Implemented |

## Data

- The database stores learner-owned data only. The question bank stays in version-controlled
  JSON ([ADR 0003](contracts/adr/0003-question-bank-stays-in-json.md)).
- Timestamps are stored with their offset, so comparisons survive a timezone change.
- Schema changes go through Alembic exclusively; CI verifies both directions.

## Reporting a vulnerability

This is a personal portfolio project with no production deployment and no real user data.
If you find a problem, open an issue describing it.
