"""
test_security.py - Tests for password hashing and JWT tokens.

No database needed: these test pure functions.
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import get_settings
from app.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ---------------- Passwords ----------------

def test_hash_is_not_the_plain_password():
    """Som's real password must never appear in the stored hash."""
    hashed = hash_password("som@1234")

    assert hashed != "som@1234"
    assert "som@1234" not in hashed
    assert hashed.startswith("$argon2id$")


def test_correct_password_is_accepted():
    """Som logs in with his real password -> accepted."""
    hashed = hash_password("som@1234")

    assert verify_password("som@1234", hashed) is True


def test_wrong_password_is_rejected():
    """Nahul tries to log in as Som with a guessed password -> rejected."""
    hashed = hash_password("som@1234")

    assert verify_password("nahul@999", hashed) is False


def test_same_password_gives_different_hashes():
    """Priya and Arjun both choose 'pass@123' -> stored hashes still differ (salt)."""
    priya_hash = hash_password("pass@123")
    arjun_hash = hash_password("pass@123")

    assert priya_hash != arjun_hash
    assert verify_password("pass@123", priya_hash) is True
    assert verify_password("pass@123", arjun_hash) is True


# ---------------- JWT tokens ----------------

def _make_token(payload_changes: dict, secret: str | None = None) -> str:
    """Helper: build a token by hand, so tests can create broken or expired ones."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": "31",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    payload.update(payload_changes)
    return jwt.encode(
        payload, secret or settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def test_token_gives_back_the_same_user_id():
    """Arjun (user 31) logs in -> his token decodes back to 31."""
    token = create_access_token(31)

    assert decode_access_token(token) == 31


def test_edited_token_is_rejected():
    """Nahul edits the end of Arjun's token -> rejected (signature no longer matches)."""
    token = create_access_token(31)
    edited = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")

    with pytest.raises(TokenError):
        decode_access_token(edited)


def test_expired_token_is_rejected():
    """Priya's token from yesterday has expired -> rejected."""
    yesterday = datetime.now(UTC) - timedelta(days=1)
    expired = _make_token({"iat": yesterday, "exp": yesterday + timedelta(minutes=60)})

    with pytest.raises(TokenError):
        decode_access_token(expired)


def test_token_signed_with_another_secret_is_rejected():
    """An attacker signs a token with their own secret -> rejected."""
    forged = _make_token({}, secret="attacker-secret-that-is-at-least-32-chars-long")

    with pytest.raises(TokenError):
        decode_access_token(forged)


def test_token_of_wrong_type_is_rejected():
    """A token labelled as some other type cannot be used to log in."""
    wrong_type = _make_token({"type": "refresh"})

    with pytest.raises(TokenError):
        decode_access_token(wrong_type)