"""Pydantic schema for one private judge test case."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TestCase(BaseModel):
    """One private test case stored as a MongoDB document."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    problem_id: UUID
    revision: int = Field(ge=1)
    ordinal: int = Field(ge=0)
    input_data: str
    expected_output: str
