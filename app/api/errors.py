"""Translate domain and service exceptions into stable HTTP responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.repositories import UserAlreadyExistsError
from app.services import (
    AuthenticationError,
    AuthorizationError,
    UserNotFoundError,
)


def register_exception_handlers(application: FastAPI) -> None:
    """Register all application-specific HTTP exception mappings."""

    @application.exception_handler(UserAlreadyExistsError)
    async def handle_user_conflict(
        _: Request,
        error: UserAlreadyExistsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": f"User with this {error.field} already exists"},
        )

    @application.exception_handler(AuthenticationError)
    async def handle_authentication_error(
        _: Request,
        __: AuthenticationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Could not validate credentials"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @application.exception_handler(AuthorizationError)
    async def handle_authorization_error(
        _: Request,
        __: AuthorizationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Insufficient permissions"},
        )

    @application.exception_handler(UserNotFoundError)
    async def handle_user_not_found(
        _: Request,
        __: UserNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "User not found"},
        )
