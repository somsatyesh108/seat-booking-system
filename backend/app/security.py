"""
security.py - Password hashing and JWT login tokens.

Rules:
- Real passwords are NEVER stored or logged. Only their Argon2 hashes.
- Tokens are signed with JWT_SECRET_KEY from .env, so they cannot be faked or edited.
"""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import get_settings

# Argon2 with the library's recommended (secure) settings.
_password_hasher = PasswordHash.recommended()


# ---------------- Passwords ----------------

def hash_password(plain_password: str) -> str:
    """
    Turn a real password into a one-way scrambled hash for storing.

    Example: hash_password("som@1234") -> "$argon2id$v=19$m=65536,t=3,p=4$..."
    Each call gives a DIFFERENT result (random salt), even for the same password.
    """
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a login attempt: does this password match the stored hash?

    Example: verify_password("som@1234", som_hash) -> True
             verify_password("wrong-pass", som_hash) -> False
    """
    return _password_hasher.verify(plain_password, hashed_password)


# ---------------- JWT tokens ----------------

class TokenError(Exception):
    """Raised when a token is fake, edited, expired or badly formed."""


def create_access_token(user_id: int) -> str:
    """
    Create a signed login token ("entry pass") for a user.

    Example: create_access_token(31) -> "eyJhbGciOiJIUzI1NiIs..."  (valid for 60 minutes)
    """
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),  # "subject": WHO this token belongs to
        "type": "access",     # what kind of token this is
        "iat": now,           # "issued at": when it was created
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),  # expiry
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """
    Check a token and return the user id inside it.

    Raises TokenError if the token is fake, edited, expired or not an access token.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],  # only accept the algorithm WE use
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.InvalidTokenError as error:
        raise TokenError("Token is invalid or expired.") from error

    if payload.get("type") != "access":
        raise TokenError("Wrong token type.")

    try:
        return int(payload["sub"])
    except (TypeError, ValueError) as error:
        raise TokenError("Token has a bad user id.") from error