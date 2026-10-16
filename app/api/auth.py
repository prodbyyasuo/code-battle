"""Registration and authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import (
    enforce_auth_rate_limit,
    get_user_service,
)
from app.schemas import (
    EmailRequest,
    MessageResponse,
    PasswordResetConfirm,
    RefreshTokenRequest,
    TokenPair,
    TokenRequest,
    UserLogin,
    UserRead,
    UserRegister,
)
from app.services import UserService

NEUTRAL_EMAIL_MESSAGE = "If an eligible account exists, an email will be sent."

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(enforce_auth_rate_limit)],
)


@auth_router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegister,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """Create a user with a non-privileged role."""
    user = await service.register(payload)
    return UserRead.model_validate(user)


@auth_router.post("/login", response_model=TokenPair)
async def login(
    payload: UserLogin,
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenPair:
    """Exchange email and password for access and refresh JWTs."""
    return await service.login(payload)


@auth_router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshTokenRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> TokenPair:
    """Rotate a valid, unused refresh token."""
    return await service.refresh(payload.refresh_token.get_secret_value())


@auth_router.post(
    "/email-verification/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_email_verification(
    payload: EmailRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    """Request verification without exposing whether the email exists."""
    await service.request_email_verification(str(payload.email))
    return MessageResponse(message=NEUTRAL_EMAIL_MESSAGE)


@auth_router.post(
    "/email-verification/confirm",
    response_model=UserRead,
)
async def confirm_email_verification(
    payload: TokenRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """Verify an email with a valid one-time token."""
    user = await service.verify_email(payload.token.get_secret_value())
    return UserRead.model_validate(user)


@auth_router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_password_reset(
    payload: EmailRequest,
    service: Annotated[UserService, Depends(get_user_service)],
) -> MessageResponse:
    """Request reset instructions with an account-neutral response."""
    await service.request_password_reset(str(payload.email))
    return MessageResponse(message=NEUTRAL_EMAIL_MESSAGE)


@auth_router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def confirm_password_reset(
    payload: PasswordResetConfirm,
    service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    """Replace a password using a valid one-time reset token."""
    await service.reset_password(
        token=payload.token.get_secret_value(),
        new_password=payload.new_password.get_secret_value(),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
