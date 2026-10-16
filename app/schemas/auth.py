"""Request and response schemas for authentication flows."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class UserLogin(BaseModel):
    """Credentials accepted by the login endpoint."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=128)


class TokenPair(BaseModel):
    """Bearer credentials returned after login or refresh."""

    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(gt=0)


class RefreshTokenRequest(BaseModel):
    """A refresh token exchanged for a rotated token pair."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: SecretStr


class EmailRequest(BaseModel):
    """Email used to request a neutral account action response."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class TokenRequest(BaseModel):
    """One-time token submitted by an email action link."""

    model_config = ConfigDict(extra="forbid")

    token: SecretStr


class PasswordResetConfirm(TokenRequest):
    """One-time reset token together with the replacement password."""

    new_password: SecretStr = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    """A response intentionally carrying no account-existence information."""

    message: str
