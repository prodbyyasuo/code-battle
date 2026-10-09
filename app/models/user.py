"""User persistence model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.domain.enums import UserRole

if TYPE_CHECKING:
    from app.models.problem import Problem
    from app.models.submission import Submission


class User(BaseModel):
    """Registered platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )
    username: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            length=20,
            create_constraint=False,
            validate_strings=True,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=UserRole.USER,
        server_default=UserRole.USER.value,
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    authored_problems: Mapped[list[Problem]] = relationship(
        "Problem",
        back_populates="author",
        lazy="raise",
        passive_deletes=True,
    )
    submissions: Mapped[list[Submission]] = relationship(
        "Submission",
        back_populates="user",
        lazy="raise",
        passive_deletes="all",
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'admin')",
            name="valid_role",
        ),
        CheckConstraint(
            "rating >= 0",
            name="non_negative_rating",
        ),
        CheckConstraint(
            "char_length(username) BETWEEN 3 AND 32",
            name="username_length",
        ),
        Index(
            "uq_users_email_lower",
            func.lower(email),
            unique=True,
        ),
        Index(
            "uq_users_username_lower",
            func.lower(username),
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r})"
