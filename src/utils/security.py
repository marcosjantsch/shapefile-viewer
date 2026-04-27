from __future__ import annotations

import hashlib
import hmac
import secrets


def create_password_hash(password: str, salt: str | None = None) -> str:
    resolved_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        resolved_salt.encode("utf-8"),
        200_000,
    ).hex()
    return f"{resolved_salt}${digest}"


def verify_password_hash(password: str, stored_hash: str) -> bool:
    if not stored_hash or "$" not in stored_hash:
        return False
    salt, expected_digest = stored_hash.split("$", 1)
    current_digest = create_password_hash(password, salt).split("$", 1)[1]
    return hmac.compare_digest(current_digest, expected_digest)
