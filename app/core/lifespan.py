from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.mongo import mongo_client
from app.db.postgres import engine
from app.db.redis import redis_client


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await redis_client.aclose()
        await mongo_client.close()
        await engine.dispose()
