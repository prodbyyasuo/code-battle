from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas import TestCase as CaseSchema
from app.schemas import TestCaseSet as CaseSetSchema

PROBLEM_ID = uuid4()


def make_case(
    *,
    problem_id: UUID = PROBLEM_ID,
    revision: int = 1,
    ordinal: int = 0,
) -> CaseSchema:
    return CaseSchema(
        problem_id=problem_id,
        revision=revision,
        ordinal=ordinal,
        input_data="2 3\n",
        expected_output="5\n",
    )


def test_test_case_accepts_valid_data() -> None:
    test_case = make_case()

    assert test_case.problem_id == PROBLEM_ID
    assert test_case.revision == 1
    assert test_case.ordinal == 0
    assert test_case.input_data == "2 3\n"
    assert test_case.expected_output == "5\n"


def test_test_case_accepts_empty_input_and_output() -> None:
    test_case = CaseSchema(
        problem_id=PROBLEM_ID,
        revision=1,
        ordinal=0,
        input_data="",
        expected_output="",
    )

    assert test_case.input_data == ""
    assert test_case.expected_output == ""


def test_test_case_rejects_non_positive_revision() -> None:
    with pytest.raises(ValidationError):
        make_case(revision=0)


def test_test_case_rejects_negative_ordinal() -> None:
    with pytest.raises(ValidationError):
        make_case(ordinal=-1)


def test_test_case_set_accepts_valid_cases() -> None:
    first_case = make_case(ordinal=0)
    second_case = make_case(ordinal=1)

    test_case_set = CaseSetSchema(
        problem_id=PROBLEM_ID,
        revision=1,
        cases=(first_case, second_case),
    )

    assert test_case_set.cases == (first_case, second_case)


def test_test_case_set_rejects_empty_cases() -> None:
    with pytest.raises(ValidationError):
        CaseSetSchema(
            problem_id=PROBLEM_ID,
            revision=1,
            cases=(),
        )


def test_test_case_set_rejects_duplicate_ordinals() -> None:
    with pytest.raises(
        ValidationError,
        match="ordinals must be unique",
    ):
        CaseSetSchema(
            problem_id=PROBLEM_ID,
            revision=1,
            cases=(
                make_case(ordinal=0),
                make_case(ordinal=0),
            ),
        )


def test_test_case_set_rejects_different_problem() -> None:
    with pytest.raises(
        ValidationError,
        match="same problem",
    ):
        CaseSetSchema(
            problem_id=PROBLEM_ID,
            revision=1,
            cases=(
                make_case(ordinal=0),
                make_case(
                    problem_id=uuid4(),
                    ordinal=1,
                ),
            ),
        )


def test_test_case_set_rejects_different_revision() -> None:
    with pytest.raises(
        ValidationError,
        match="same revision",
    ):
        CaseSetSchema(
            problem_id=PROBLEM_ID,
            revision=1,
            cases=(
                make_case(ordinal=0),
                make_case(revision=2, ordinal=1),
            ),
        )


def test_test_case_set_rejects_ordinal_gap() -> None:
    with pytest.raises(
        ValidationError,
        match="ordered and contiguous",
    ):
        CaseSetSchema(
            problem_id=PROBLEM_ID,
            revision=1,
            cases=(
                make_case(ordinal=0),
                make_case(ordinal=2),
            ),
        )
