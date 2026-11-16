"""
security.py - Password hashing (now) and JWT login tokens (coming in Step 3.3).

Rule: real passwords are NEVER stored or logged. Only their Argon2 hashes.
"""

from pwdlib import PasswordHash

# Argon2 with the library's recommended (secure) settings.
_password_hasher = PasswordHash.recommended()


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