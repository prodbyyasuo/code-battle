"""Integration tests for the MongoDB test-case repository."""

from uuid import UUID, uuid4

import pytest

from app.repositories import (
    TestCaseRepository as RepositoryProtocol,
)
from app.repositories import (
    TestCaseSetAlreadyExistsError as SetAlreadyExistsError,
)
from app.schemas import TestCase as CaseSchema
from app.schemas import TestCaseSet as CaseSetSchema

pytestmark = pytest.mark.integration


def make_test_case_set(
    *,
    problem_id: UUID,
    revision: int,
) -> CaseSetSchema:
    return CaseSetSchema(
        problem_id=problem_id,
        revision=revision,
        cases=(
            CaseSchema(
                problem_id=problem_id,
                revision=revision,
                ordinal=0,
                input_data="2 3\n",
                expected_output="5\n",
            ),
            CaseSchema(
                problem_id=problem_id,
                revision=revision,
                ordinal=1,
                input_data="10 -4\n",
                expected_output="6\n",
            ),
        ),
    )


async def test_create_and_get_by_revision(
    test_case_repository: RepositoryProtocol,
) -> None:
    problem_id = uuid4()
    expected = make_test_case_set(
        problem_id=problem_id,
        revision=1,
    )

    created = await test_case_repository.create(expected)
    loaded = await test_case_repository.get_by_revision(
        problem_id=problem_id,
        revision=1,
    )

    assert created == expected
    assert loaded == expected


async def test_get_by_revision_returns_none_when_missing(
    test_case_repository: RepositoryProtocol,
) -> None:
    loaded = await test_case_repository.get_by_revision(
        problem_id=uuid4(),
        revision=1,
    )

    assert loaded is None


async def test_get_latest_returns_highest_revision(
    test_case_repository: RepositoryProtocol,
) -> None:
    problem_id = uuid4()
    first_revision = make_test_case_set(
        problem_id=problem_id,
        revision=1,
    )
    second_revision = make_test_case_set(
        problem_id=problem_id,
        revision=2,
    )

    await test_case_repository.create(first_revision)
    await test_case_repository.create(second_revision)

    loaded = await test_case_repository.get_latest(problem_id)

    assert loaded == second_revision


async def test_get_latest_returns_none_when_missing(
    test_case_repository: RepositoryProtocol,
) -> None:
    loaded = await test_case_repository.get_latest(uuid4())

    assert loaded is None


async def test_create_rejects_existing_revision(
    test_case_repository: RepositoryProtocol,
) -> None:
    problem_id = uuid4()
    test_case_set = make_test_case_set(
        problem_id=problem_id,
        revision=1,
    )

    await test_case_repository.create(test_case_set)

    with pytest.raises(SetAlreadyExistsError) as error:
        await test_case_repository.create(test_case_set)

    assert error.value.problem_id == problem_id
    assert error.value.revision == 1

    loaded = await test_case_repository.get_by_revision(
        problem_id=problem_id,
        revision=1,
    )
    assert loaded == test_case_set
