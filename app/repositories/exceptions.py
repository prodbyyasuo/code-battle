"""Repository-layer exceptions."""

from uuid import UUID


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