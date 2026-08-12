# Security posture

This application teaches CompTIA Security+ material, so it holds itself to the practices it
describes. Each control below is mapped to the SY0-701 domain it belongs to.

Controls marked **planned** are recorded decisions, not implemented behaviour. They are listed
so the gap between the current state and the target state stays visible.

## Application

| Control | Status | SY0-701 domain |
|---|---|---|
| Answers and explanations are never returned by browsing endpoints | Implemented | 3.0 Security Architecture |
| Request and response validation on every endpoint via Pydantic schemas | Implemented | 2.0 Threats and Mitigations |
| Parameterized queries only; no string-built SQL | Implemented | 2.0 Threats and Mitigations |
| Interactive API documentation disabled in production | Implemented | 3.0 Security Architecture |
| Argon2 password hashing | Planned | 1.0 General Security Concepts |
| `HttpOnly`, `Secure`, `SameSite=Lax` session cookies rather than tokens in browser storage | Planned | 1.0 General Security Concepts |
| Double-submit CSRF tokens on state-changing requests | Planned | 2.0 Threats and Mitigations |
| Rate limiting and lockout on authentication endpoints | Planned | 4.0 Security Operations |

The session cookie decision and its trade-offs are recorded in
[ADR 0004](contracts/adr/0004-session-cookies-instead-of-jwt-in-storage.md).

## Response headers

Set by `SecurityHeadersMiddleware` on every response:

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
| Runs as an unprivileged user (`appuser`, uid 999) | Implemented |
| Multi-stage build; no compilers or build tooling in the runtime image | Implemented |
| CI asserts the image does not run as root | Implemented |
| `pip-audit` fails the build on known vulnerable dependencies | Implemented |
| Dependencies pinned to compatible ranges | Implemented |
| Container image scanning (Trivy) | Planned |
| Static analysis (CodeQL) and secret scanning (Gitleaks) | Planned |
| Dependabot update automation | Planned |

## Data

- The database stores learner-owned data only. The question bank stays in version-controlled
  JSON ([ADR 0003](contracts/adr/0003-question-bank-stays-in-json.md)).
- Timestamps are stored with their offset, so comparisons survive a timezone change.
- Schema changes go through Alembic exclusively; CI verifies both directions.

## Reporting a vulnerability

This is a personal portfolio project with no production deployment and no real user data.
If you find a problem, open an issue describing it.
