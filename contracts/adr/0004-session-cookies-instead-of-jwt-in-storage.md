# 4. Session cookies instead of a token in browser storage

- Status: Accepted
- Date: 2026-08-12

## Context

The common tutorial approach is a JSON Web Token held in `localStorage` and attached as an
`Authorization` header.

Anything in `localStorage` is readable by JavaScript, so a single cross-site scripting flaw
discloses the credential. This application exists to teach that exact material.

## Decision

Authenticate with a server-side session referenced by an `HttpOnly`, `Secure`,
`SameSite=Lax` cookie. Protect state-changing requests with a double-submit CSRF token.

## Consequences

- Script injected into the page cannot read the session credential.
- Logout revokes server-side, unlike a self-contained token that stays valid until it expires.
- CSRF protection becomes necessary, which a bearer token would not have required. The
  frontend sends `credentials: 'include'` and echoes the CSRF token in `X-CSRF-Token` on
  unsafe methods.
- `CORS_ORIGINS` must list the frontend origin exactly; wildcards are incompatible with
  credentialed requests.
- Only an HMAC-SHA256 digest of the session token is stored, keyed by `SECRET_KEY`, so a
  database disclosure does not yield usable sessions. A slow key-derivation function would add
  cost to every authenticated request while protecting nothing, because the token is already
  high-entropy and random. Rotating the key signs everyone out.
- Authentication requires a database round trip per request, unlike a self-contained token.
  That cost buys revocation, which is the property that matters here.
