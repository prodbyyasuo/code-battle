"""Pydantic schemas for users and registration."""

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
)

from app.domain import UserRole


class UserRegister(BaseModel):
    """Input accepted by the registration endpoint."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern="^[a-zA-Z0-9_-]+$",
    )
    password: SecretStr = Field(
        min_length=8,
        max_length=128,
    )


class UserRead(BaseModel):
    """Private representation returned to the authenticated user."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: UUID
    email: EmailStr
    username: str
    role: UserRole
    rating: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
