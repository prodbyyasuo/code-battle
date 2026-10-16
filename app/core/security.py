"""Password hashing utilities."""

import asyncio

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

_password_hash = PasswordHash.recommended()

# Verifying this valid hash when an email is absent keeps login timing closer
# to the existing-user path and makes account enumeration harder.
DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "ox3rJO5h9w6snz8sG5lkjg$"
    "Rxu+8q0gaQiK7Pon1cGfiAB4lx3s8P2inM7EC05Ih0o"
)


async def hash_password(password: str) -> str:
    """Hash a password."""
    return await asyncio.to_thread(
        _password_hash.hash,
        password,
    )


async def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its stored Argon2 hash."""
    try:
        return await asyncio.to_thread(
            _password_hash.verify,
            password,
            password_hash,
        )
    except UnknownHashError:
        return False
