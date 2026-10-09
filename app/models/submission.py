"""Submitted solution persistence model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.domain.enums import SubmissionStatus

if TYPE_CHECKING:
    from app.models.problem import Problem
    from app.models.submission_case import SubmissionCase
    from app.models.user import User


class Submission(BaseModel):
    """One immutable source-code attempt and its aggregate result."""

    __tablename__ = "submissions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    problem_id: Mapped[UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="RESTRICT"),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    source_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(
            SubmissionStatus,
            name="submission_status",
            native_enum=False,
            length=32,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=SubmissionStatus.QUEUED,
        server_default=SubmissionStatus.QUEUED.value,
        nullable=False,
    )
    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    problem_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    test_set_revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="submissions",
        lazy="raise",
    )
    problem: Mapped[Problem] = relationship(
        "Problem",
        back_populates="submissions",
        lazy="raise",
    )
    cases: Mapped[list[SubmissionCase]] = relationship(
        "SubmissionCase",
        back_populates="submission",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'queued', 'running', 'accepted', 'wrong_answer', "
            "'time_limit_exceeded', 'memory_limit_exceeded', "
            "'runtime_error', 'system_error'"
            ")",
            name="valid_status",
        ),
        CheckConstraint(
            "score BETWEEN 0 AND 100",
            name="valid_score",
        ),
        CheckConstraint(
            "problem_version > 0",
            name="positive_problem_version",
        ),
        CheckConstraint(
            "test_set_revision > 0",
            name="positive_test_set_revision",
        ),
        CheckConstraint(
            "char_length(btrim(language)) > 0",
            name="non_empty_language",
        ),
        CheckConstraint(
            "char_length(source_code) > 0",
            name="non_empty_source_code",
        ),
        CheckConstraint(
            "finished_at IS NULL OR started_at IS NULL "
            "OR finished_at >= started_at",
            name="valid_execution_window",
        ),
        Index(
            "ix_submissions_user_created_at",
            "user_id",
            "created_at",
        ),
        Index(
            "ix_submissions_problem_created_at",
            "problem_id",
            "created_at",
        ),
        Index(
            "ix_submissions_status_created_at",
            "status",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return f"Submission(id={self.id!r}, status={self.status!r})"
