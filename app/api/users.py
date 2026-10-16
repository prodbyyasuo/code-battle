"""Authenticated user endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_admin_user,
    get_current_user,
    get_user_service,
)
from app.models import User
from app.schemas import UserRead
from app.services import UserService

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("/me", response_model=UserRead)
async def read_current_user(
    user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    """Return the private profile of the authenticated user."""
    return UserRead.model_validate(user)


@users_router.get("/{user_id}", response_model=UserRead)
async def read_user_as_admin(
    user_id: UUID,
    _: Annotated[User, Depends(get_admin_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """Return a user to administrators only."""
    user = await service.get_user(user_id)
    return UserRead.model_validate(user)
