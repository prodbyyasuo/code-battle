"""Application health endopoints."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.db.mongo import ping_mongodb
from app.db.postgres import engine
from app.db.redis import ping_redis

logger = logging.getLogger(__name__)

health_router = APIRouter(prefix="/health", tags=["health"])


async def ping_postgresql() -> None:
    """Raise a SQLAlchemy exception when PostgreSQL is unavailable."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


@health_router.get("/live", include_in_schema=False)
async def liveness() -> dict[str, str]:
    """Report whether the API process is running."""
    return {"status": "ok"}


@health_router.get("/ready", include_in_schema=False)
async def readiness() -> dict[str, str]:
    """Report whether all required infrastructure is available."""
    try:
        async with asyncio.timeout(5):
            await ping_postgresql()
            await ping_mongodb()
            await ping_redis()
    except Exception:
        logger.exception("Readiness check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready",
        ) from None

    return {"status": "ok"}
