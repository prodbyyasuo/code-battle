"""Fixtures for integration tests."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.mongo import MongoDocument
from app.db.postgres import async_session_factory
from app.repositories import TestCaseRepository, UserRepository
from app.repositories.mongo import MongoTestCaseRepository
from app.repositories.postgres import SQLAlchemyUserRepository
from mongo_migrations.runner import run_migrations


@pytest_asyncio.fixture
async def mongo_database() -> AsyncIterator[AsyncDatabase[MongoDocument]]:
    settings = get_settings()
    database_name = f"{settings.mongodb_database}_pytest_{uuid4().hex}"

    client: AsyncMongoClient[MongoDocument] = AsyncMongoClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=(
            settings.mongodb_server_selection_timeout_ms
        ),
        tz_aware=True,
        uuidRepresentation="standard",
    )

    await client.admin.command({"ping": 1})
    database = client[database_name]
    await run_migrations(database)

    try:
        yield database
    finally:
        await client.drop_database(database_name)
        await client.close()


@pytest.fixture
def test_case_repository(
    mongo_database: AsyncDatabase[MongoDocument],
) -> TestCaseRepository:
    repository: TestCaseRepository = MongoTestCaseRepository(mongo_database)
    return repository


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a PostgreSQL session rolled back after each test."""
    async with async_session_factory() as session:
        transaction = await session.begin()

        try:
            yield session
        finally:
            if transaction.is_active:
                await transaction.rollback()


@pytest.fixture
def user_repository(
    db_session: AsyncSession,
) -> UserRepository:
    repository: UserRepository = SQLAlchemyUserRepository(db_session)
    return repository
