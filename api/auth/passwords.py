"""Password hashing — PBKDF2-HMAC-SHA256, compatible with erpclaw_lib."""

import hashlib
import hmac
import os
import secrets


ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return f"pbkdf2:{ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        _, rest = password_hash.split(":", 1)
        iterations_str, salt, stored_hash = rest.split("$", 2)
        iterations = int(iterations_str)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
        return hmac.compare_digest(dk.hex(), stored_hash)
    except (ValueError, AttributeError):
        return False


def validate_password(password: str) -> str | None:
    """Validate password strength. Returns error message or None if valid."""
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return "Password must contain at least 1 uppercase letter"
    if not any(c.islower() for c in password):
        return "Password must contain at least 1 lowercase letter"
    if not any(c.isdigit() for c in password):
        return "Password must contain at least 1 digit"
    return None
