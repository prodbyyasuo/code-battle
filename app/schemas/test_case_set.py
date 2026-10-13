"""Pydantic schema for a validated revision of private test cases."""

from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.test_case import TestCase


class TestCaseSet(BaseModel):
    """An ordered collection of test cases for one problem revision."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    problem_id: UUID
    revision: int = Field(ge=1)
    cases: tuple[TestCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_cases(self) -> Self:
        """Ensure all cases belong to this set and form a stable order."""
        if any(case.problem_id != self.problem_id for case in self.cases):
            raise ValueError("all test cases must belong to the same problem")

        if any(case.revision != self.revision for case in self.cases):
            raise ValueError("all test cases must belong to the same revision")

        ordinals = tuple(case.ordinal for case in self.cases)
        if len(set(ordinals)) != len(ordinals):
            raise ValueError("test case ordinals must be unique")

        expected_ordinals = tuple(range(len(self.cases)))
        if ordinals != expected_ordinals:
            raise ValueError(
                "test case ordinals must be ordered and contiguous "
                "starting at zero"
            )

        return self
