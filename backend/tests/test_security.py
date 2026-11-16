"""
test_security.py - Tests for password hashing.

No database needed: these test pure functions.
"""

from app.security import hash_password, verify_password


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