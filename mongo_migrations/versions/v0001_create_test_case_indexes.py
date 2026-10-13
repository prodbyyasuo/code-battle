"""Create indexes for private test-case documents."""

from pymongo import ASCENDING
from pymongo.asynchronous.database import AsyncDatabase

from app.db.mongo import MongoDocument
from app.repositories.mongo.test_case import (
    TEST_CASES_COLLECTION,
)
from mongo_migrations.base import MongoMigration

INDEX_NAME = "uq_test_cases_problem_revision_ordinal"


async def up(
    database: AsyncDatabase[MongoDocument],
) -> None:
    collection = database[TEST_CASES_COLLECTION]

    await collection.create_index(
        [
            ("problem_id", ASCENDING),
            ("revision", ASCENDING),
            ("ordinal", ASCENDING),
        ],
        name=INDEX_NAME,
        unique=True,
    )


migration = MongoMigration(
    version=1,
    name="create_test_case_indexes",
    up=up,
)
