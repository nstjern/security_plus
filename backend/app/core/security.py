"""Password hashing, session tokens, and constant-time comparison.

Argon2id is the current OWASP recommendation for password storage. Session tokens are
different: they are already high-entropy random values, so they are keyed-hashed rather than
run through a slow KDF, which would add cost on every authenticated request and guard against
nothing. The key comes from ``SECRET_KEY``, so a stolen database alone cannot be used to
confirm a guessed token. Rotating that key invalidates every existing session.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Defaults track the argon2-cffi maintainers' reading of the OWASP cheat sheet.
_password_hasher = PasswordHasher()

SESSION_TOKEN_BYTES = 48
CSRF_TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Return whether the password matches, without leaking which check failed."""
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """True when the stored hash predates the current cost parameters."""
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def generate_session_token() -> str:
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(CSRF_TOKEN_BYTES)


def hash_token(token: str, *, key: str) -> str:
    """Digest a session token so a database disclosure does not yield usable sessions."""
    return hmac.new(key.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def tokens_match(left: str, right: str) -> bool:
    return secrets.compare_digest(left, right)
