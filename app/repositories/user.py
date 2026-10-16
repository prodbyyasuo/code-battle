"""Repository contract for users."""

from typing import Protocol
from uuid import UUID

from app.models import User


class UserRepository(Protocol):
    """Persistence operations for users."""

    async def create(
        self,
        *,
        email: str,
        username: str,
        password_hash: str,
    ) -> User:
        """Create and flush a user without committing."""
        ...

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        """Return a user by identifier."""
        ...

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        """Return a user by case-insensitive email."""
        ...

    async def get_by_username(
        self,
        username: str,
    ) -> User | None:
        """Return a user by case-insensitive username."""
        ...

    async def mark_verified(
        self,
        user_id: UUID,
    ) -> User | None:
        """Mark a user email as verified without committing."""
        ...

    async def update_password(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> User | None:
        """Replace a password hash without committing."""
        ...
