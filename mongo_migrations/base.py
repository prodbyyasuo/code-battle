"""Core types for MongoDB migrations."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongo import MongoDocument

type MigrationFunction = Callable[
    [AsyncDatabase[MongoDocument]],
    Awaitable[None],
]


@dataclass(frozen=True, slots=True)
class MongoMigration:
    """One sequential and idempotent MongoDB migration."""

    version: int
    name: str
    up: MigrationFunction
