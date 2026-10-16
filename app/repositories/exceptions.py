"""Repository-layer exceptions."""

from typing import Literal
from uuid import UUID

type UserConflictField = Literal["email", "username"]


class RepositoryError(Exception):
    """Base exception for repository operations."""


class TestCaseSetAlreadyExistsError(RepositoryError):
    """A test-set revision already exists for the problem."""

    def __init__(
        self,
        problem_id: UUID,
        revision: int,
    ) -> None:
        self.problem_id = problem_id
        self.revision = revision
        super().__init__(
            f"Test-case set already exists for problem "
            f"{problem_id}, revision {revision}"
        )


class UserAlreadyExistsError(RepositoryError):
    """A user with the unique field already exists."""

    def __init__(
        self,
        field: UserConflictField,
    ) -> None:
        self.field = field
        super().__init__(f"User with this {field} already exists")
