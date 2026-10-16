"""SQLAlchemy implementation of the user repository."""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories.exceptions import (
    UserAlreadyExistsError,
    UserConflictField,
)

USER_CONFLICT_CONSTRAINTS: dict[str, UserConflictField] = {
    "uq_users_email_lower": "email",
    "uq_users_username_lower": "username",
}


def _get_constraint_name(
    error: IntegrityError,
) -> str | None:
    current: BaseException | None = error.orig

    while current is not None:
        constraint_name = getattr(
            current,
            "constraint_name",
            None,
        )
        if isinstance(constraint_name, str):
            return constraint_name

        current = current.__cause__ or current.__context__

    return None


class SQLAlchemyUserRepository:
    """Persist users through an async SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        email: str,
        username: str,
        password_hash: str,
    ) -> User:
        user = User(
            email=email.strip().lower(),
            username=username.strip(),
            password_hash=password_hash,
        )
        self._session.add(user)

        try:
            await self._session.flush()
        except IntegrityError as error:
            constraint_name = _get_constraint_name(error)
            field = USER_CONFLICT_CONSTRAINTS.get(constraint_name or "")

            if field is None:
                raise

            raise UserAlreadyExistsError(field) from error

        await self._session.refresh(user)
        return user

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        statement = select(User).where(User.id == user_id)
        return await self._session.scalar(statement)

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        statement = select(User).where(
            func.lower(User.email) == email.strip().lower()
        )
        return await self._session.scalar(statement)

    async def get_by_username(
        self,
        username: str,
    ) -> User | None:
        statement = select(User).where(
            func.lower(User.username) == username.strip().lower()
        )
        return await self._session.scalar(statement)

    async def mark_verified(
        self,
        user_id: UUID,
    ) -> User | None:
        statement = (
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True)
            .returning(User)
        )
        return await self._session.scalar(statement)

    async def update_password(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> User | None:
        statement = (
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash)
            .returning(User)
        )
        return await self._session.scalar(statement)
