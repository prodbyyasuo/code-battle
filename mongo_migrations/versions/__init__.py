"""Ordered registry of MongoDB migrations."""

from mongo_migrations.base import MongoMigration
from mongo_migrations.versions.v0001_create_test_case_indexes import (
    migration as v0001,
)

MIGRATIONS: tuple[MongoMigration, ...] = (v0001,)

__all__ = ("MIGRATIONS",)
