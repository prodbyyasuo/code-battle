"""Algorithmic problem persistence model."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from app.domain.enums import ProblemDifficulty

if TYPE_CHECKING:
    from app.models.submission import Submission
    from app.models.user import User


class Problem(BaseModel):
    """Public problem metadata and statement."""

    __tablename__ = "problems"

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    difficulty: Mapped[ProblemDifficulty] = mapped_column(
        Enum(
            ProblemDifficulty,
            name="problem_difficulty",
            native_enum=False,
            length=20,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    time_limit_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    memory_limit_mb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default=text("1"),
        nullable=False,
    )
    author_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    author: Mapped[User | None] = relationship(
        "User",
        back_populates="authored_problems",
        lazy="raise",
    )
    submissions: Mapped[list[Submission]] = relationship(
        "Submission",
        back_populates="problem",
        lazy="raise",
        passive_deletes="all",
    )

    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="valid_difficulty",
        ),
        CheckConstraint(
            "time_limit_ms > 0",
            name="positive_time_limit",
        ),
        CheckConstraint(
            "memory_limit_mb > 0",
            name="positive_memory_limit",
        ),
        CheckConstraint(
            "version > 0",
            name="positive_version",
        ),
        CheckConstraint(
            "char_length(btrim(title)) > 0",
            name="non_empty_title",
        ),
        CheckConstraint(
            "char_length(btrim(statement)) > 0",
            name="non_empty_statement",
        ),
        CheckConstraint(
            "slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="slug_format",
        ),
        Index(
            "ix_problems_published_difficulty",
            "is_published",
            "difficulty",
        ),
    )

    def __repr__(self) -> str:
        return f"Problem(id={self.id!r}, slug={self.slug!r})"
