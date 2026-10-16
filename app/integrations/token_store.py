"""One-time JWT use tracking backed by Redis."""

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from redis.asyncio import Redis

from app.domain import TokenType


class OneTimeTokenStore(Protocol):
    """Atomic contract used to prevent token replay."""

    async def consume(
        self,
        *,
        token_type: TokenType,
        jti: UUID,
        expires_at: datetime,
    ) -> bool:
        """Return true only for the first use before expiration."""
        ...


class RedisOneTimeTokenStore:
    """Store consumed token identifiers until their JWTs expire."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def consume(
        self,
        *,
        token_type: TokenType,
        jti: UUID,
        expires_at: datetime,
    ) -> bool:
        ttl = max(
            1,
            int((expires_at - datetime.now(UTC)).total_seconds()),
        )
        created = await self._redis.set(
            f"auth:consumed:{token_type.value}:{jti}",
            "1",
            ex=ttl,
            nx=True,
        )
        return bool(created)
