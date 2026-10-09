"""MongoDB client and database access."""

from typing import Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings

type MongoDocument = dict[str, Any]

settings = get_settings()

mongo_client: AsyncMongoClient[MongoDocument] = AsyncMongoClient(
    settings.mongodb_url,
    serverSelectionTimeoutMS=(settings.mongodb_server_selection_timeout_ms),
    tz_aware=True,
    uuidRepresentation="standard",
)

mongo_database: AsyncDatabase[MongoDocument] = mongo_client[
    settings.mongodb_database
]


def get_mongo_database() -> AsyncDatabase[MongoDocument]:
    """Return the shared database handle for repository dependencies."""
    return mongo_database


async def ping_mongodb() -> None:
    """Raise a PyMongo exception when MongoDB is unavailable."""
    await mongo_client.admin.command({"ping": 1})
