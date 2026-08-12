"""Password hashing and token handling."""

from __future__ import annotations

from app.core.security import (
    generate_csrf_token,
    generate_session_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    tokens_match,
    verify_password,
)

PASSWORD = "correct-horse-battery"
KEY = "a-key-used-only-by-these-tests"


def test_hashing_uses_argon2id() -> None:
    assert hash_password(PASSWORD).startswith("$argon2id$")


def test_the_same_password_hashes_differently_every_time() -> None:
    """A per-hash salt means identical passwords do not produce identical hashes."""
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


def test_verification_accepts_the_right_password() -> None:
    assert verify_password(hash_password(PASSWORD), PASSWORD)


def test_verification_rejects_the_wrong_password() -> None:
    assert not verify_password(hash_password(PASSWORD), "something-else-entirely")


def test_verification_rejects_a_malformed_hash_instead_of_raising() -> None:
    assert not verify_password("not-a-hash", PASSWORD)


def test_fresh_hashes_do_not_need_rehashing() -> None:
    assert not password_needs_rehash(hash_password(PASSWORD))


def test_unreadable_hashes_are_treated_as_needing_a_rehash() -> None:
    assert password_needs_rehash("not-a-hash")


def test_session_tokens_are_unpredictable_and_long() -> None:
    tokens = {generate_session_token() for _ in range(50)}
    assert len(tokens) == 50
    assert all(len(token) >= 60 for token in tokens)


def test_csrf_tokens_are_unique() -> None:
    assert len({generate_csrf_token() for _ in range(50)}) == 50


def test_token_hashing_is_deterministic_and_distinguishing() -> None:
    assert hash_token("abc", key=KEY) == hash_token("abc", key=KEY)
    assert hash_token("abc", key=KEY) != hash_token("abd", key=KEY)
    assert len(hash_token("abc", key=KEY)) == 64


def test_token_digests_depend_on_the_secret_key() -> None:
    """Rotating the key invalidates every stored session, which is the intended effect."""
    assert hash_token("abc", key=KEY) != hash_token("abc", key="a-different-key")


def test_token_comparison_matches_only_identical_values() -> None:
    assert tokens_match("abc", "abc")
    assert not tokens_match("abc", "abd")
    assert not tokens_match("abc", "")
