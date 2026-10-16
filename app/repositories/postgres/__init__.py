"""PostgreSQL repository implementations."""

from app.repositories.postgres.user import (
    SQLAlchemyUserRepository,
)

__all__ = ("SQLAlchemyUserRepository",)
