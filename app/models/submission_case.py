"""Per-test submission result persistence model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.domain.enums import SubmissionCaseVerdict

if TYPE_CHECKING:
    from app.models.submission import Submission


class SubmissionCase(BaseModel):
    """Execution result for one hidden test case."""

    __tablename__ = "submission_cases"

    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    ordinal: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    verdict: Mapped[SubmissionCaseVerdict] = mapped_column(
        Enum(
            SubmissionCaseVerdict,
            name="submission_case_verdict",
            native_enum=False,
            length=32,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    memory_kb: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    submission: Mapped[Submission] = relationship(
        "Submission",
        back_populates="cases",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "verdict IN ("
            "'passed', 'wrong_answer', 'time_limit_exceeded', "
            "'memory_limit_exceeded', 'runtime_error', "
            "'system_error', 'skipped'"
            ")",
            name="valid_verdict",
        ),
        CheckConstraint(
            "ordinal >= 0",
            name="non_negative_ordinal",
        ),
        CheckConstraint(
            "duration_ms IS NULL OR duration_ms >= 0",
            name="non_negative_duration",
        ),
        CheckConstraint(
            "memory_kb IS NULL OR memory_kb >= 0",
            name="non_negative_memory",
        ),
        UniqueConstraint(
            "submission_id",
            "ordinal",
            name="submission_ordinal",
        ),
    )

    def __repr__(self) -> str:
        return (
            "SubmissionCase("
            f"id={self.id!r}, ordinal={self.ordinal!r}, "
            f"verdict={self.verdict!r})"
        )
