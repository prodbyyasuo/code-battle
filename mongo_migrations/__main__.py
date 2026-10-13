"""Command-line entry point for MongoDB migrations."""

import asyncio

from app.db.mongo import mongo_client, mongo_database
from mongo_migrations.runner import run_migrations


async def main() -> None:
    """Apply pending migrations using the configured MongoDB database."""
    try:
        applied = await run_migrations(mongo_database)
    finally:
        await mongo_client.close()

    if not applied:
        print("MongoDB is up to date")
        return

    for migration in applied:
        print(f"Applied {migration.version:04d}: {migration.name}")


if __name__ == "__main__":
    asyncio.run(main())
