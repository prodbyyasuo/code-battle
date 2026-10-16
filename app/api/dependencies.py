"""FastAPI dependency graph for authentication and authorization."""

import time
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.tokens import TokenService
from app.db.postgres import get_db_session
from app.db.redis import redis_client
from app.domain import UserRole
from app.integrations import CeleryEmailDispatcher, RedisOneTimeTokenStore
from app.models import User
from app.repositories.postgres import SQLAlchemyUserRepository
from app.services import AuthenticationError, AuthorizationError, UserService

bearer_scheme = HTTPBearer(auto_error=False)


def get_app_settings() -> Settings:
    """Expose cached settings through an overridable dependency."""
    return get_settings()


def get_redis_client() -> Redis:
    """Expose the shared async Redis client."""
    return redis_client


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> UserService:
    """Build one request-scoped user service."""
    return UserService(
        session=session,
        users=SQLAlchemyUserRepository(session),
        tokens=TokenService(settings),
        token_store=RedisOneTimeTokenStore(redis),
        email_dispatcher=CeleryEmailDispatcher(settings),
    )


async def enforce_auth_rate_limit(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> None:
    """Apply a small fixed-window limit per client and auth endpoint."""
    window = settings.auth_rate_limit_window_seconds
    now = int(time.time())
    bucket = now // window
    client = request.client.host if request.client else "unknown"
    key = f"rate-limit:auth:{client}:{request.url.path}:{bucket}"

    try:
        async with redis.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, window + 1)
            result = await pipeline.execute()
    except RedisError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from error

    request_count = int(result[0])
    if request_count > settings.auth_rate_limit_requests:
        retry_after = window - (now % window)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts",
            headers={"Retry-After": str(retry_after)},
        )


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    """Resolve the current user from an access Bearer token."""
    if credentials is None:
        raise AuthenticationError("Authentication is required")
    return await service.get_current_user(credentials.credentials)


def require_roles(
    *roles: UserRole,
) -> Callable[..., Awaitable[User]]:
    """Create a dependency that accepts only the selected roles."""

    async def dependency(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role not in roles:
            raise AuthorizationError("Insufficient permissions")
        return user

    return dependency


get_admin_user = require_roles(UserRole.ADMIN)
