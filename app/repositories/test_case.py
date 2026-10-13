"""Repository contract for private test-case sets."""

from typing import Protocol
from uuid import UUID

from app.schemas import TestCaseSet


class TestCaseRepository(Protocol):
    """Persistence operations for immutable test-set revisions."""

    async def create(
        self,
        test_case_set: TestCaseSet,
    ) -> TestCaseSet:
        """Store a new immutable test-set revision."""
        ...

    async def get_by_revision(
        self,
        problem_id: UUID,
        revision: int,
    ) -> TestCaseSet | None:
        """Return one revision or None when it does not exist."""
        ...

    async def get_latest(
        self,
        problem_id: UUID,
    ) -> TestCaseSet | None:
        """Return the newest revision for a problem."""
        ...
