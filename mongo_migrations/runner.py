"""Sequential runner for forward-only MongoDB migrations."""

from collections.abc import Sequence
from contextlib import suppress
from datetime import UTC, datetime

from pymongo import ASCENDING
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from app.db.mongo import MongoDocument
from mongo_migrations.base import MongoMigration
from mongo_migrations.versions import MIGRATIONS

MIGRATIONS_COLLECTION = "_schema_migrations"
VERSION_INDEX_NAME = "uq_schema_migrations_version"


def _validate_registry(
    migrations: Sequence[MongoMigration],
) -> None:
    versions = tuple(migration.version for migration in migrations)
    expected_versions = tuple(range(1, len(migrations) + 1))

    if versions != expected_versions:
        raise RuntimeError(
            "MongoDB migration versions must be unique, ordered, "
            "and consecutive starting at 1"
        )

    names = tuple(migration.name for migration in migrations)
    if len(set(names)) != len(names):
        raise RuntimeError("MongoDB migration names must be unique")


async def _get_applied_versions(
    collection: AsyncCollection[MongoDocument],
) -> set[int]:
    documents = await collection.find(
        {},
        {"_id": 0, "version": 1},
    ).to_list()

    applied_versions: set[int] = set()
    for document in documents:
        version = document.get("version")
        if type(version) is not int or version < 1:
            raise RuntimeError(
                "MongoDB migration history contains an invalid version"
            )
        applied_versions.add(version)

    return applied_versions


async def run_migrations(
    database: AsyncDatabase[MongoDocument],
    migrations: Sequence[MongoMigration] = MIGRATIONS,
) -> tuple[MongoMigration, ...]:
    """Apply every pending migration and return those applied now."""
    _validate_registry(migrations)

    collection: AsyncCollection[MongoDocument] = database[
        MIGRATIONS_COLLECTION
    ]
    await collection.create_index(
        [("version", ASCENDING)],
        name=VERSION_INDEX_NAME,
        unique=True,
    )

    applied_versions = await _get_applied_versions(collection)
    registered_versions = {migration.version for migration in migrations}
    unknown_versions = applied_versions - registered_versions
    if unknown_versions:
        versions = ", ".join(
            str(version) for version in sorted(unknown_versions)
        )
        raise RuntimeError(
            f"Database contains unknown MongoDB migrations: {versions}"
        )

    applied_now: list[MongoMigration] = []
    for migration in migrations:
        if migration.version in applied_versions:
            continue

        await migration.up(database)

        # Another runner may record the same idempotent migration first.
        with suppress(DuplicateKeyError):
            await collection.insert_one(
                {
                    "version": migration.version,
                    "name": migration.name,
                    "applied_at": datetime.now(UTC),
                }
            )

        applied_now.append(migration)

    return tuple(applied_now)
