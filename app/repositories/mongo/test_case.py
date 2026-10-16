"""PyMongo implementation of the test-case repository."""

from uuid import UUID

from pymongo import DESCENDING
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import BulkWriteError

from app.db.mongo import MongoDocument
from app.repositories.exceptions import (
    TestCaseSetAlreadyExistsError,
)
from app.schemas import TestCase, TestCaseSet

TEST_CASES_COLLECTION = "test_cases"


def _contains_duplicate_key(error: BulkWriteError) -> bool:
    write_errors = error.details.get("writeErrors", ())

    return any(
        write_error.get("code") == 11000 for write_error in write_errors
    )


class MongoTestCaseRepository:
    """Store and retrieve private test cases in MongoDB."""

    def __init__(
        self,
        database: AsyncDatabase[MongoDocument],
    ) -> None:
        self._collection: AsyncCollection[MongoDocument] = (
            database.get_collection(TEST_CASES_COLLECTION)
        )

    async def create(
        self,
        test_case_set: TestCaseSet,
    ) -> TestCaseSet:
        documents = [
            test_case.model_dump(mode="python")
            for test_case in test_case_set.cases
        ]

        try:
            await self._collection.insert_many(
                documents,
                ordered=True,
            )
        except BulkWriteError as error:
            if not _contains_duplicate_key(error):
                raise

            raise TestCaseSetAlreadyExistsError(
                problem_id=test_case_set.problem_id,
                revision=test_case_set.revision,
            ) from error

        return test_case_set

    async def get_by_revision(
        self,
        problem_id: UUID,
        revision: int,
    ) -> TestCaseSet | None:
        cursor = self._collection.find(
            {
                "problem_id": problem_id,
                "revision": revision,
            },
            {
                "_id": 0,
            },
        ).sort("ordinal", 1)

        documents = await cursor.to_list()

        if not documents:
            return None

        cases = tuple(
            TestCase.model_validate(document) for document in documents
        )

        return TestCaseSet(
            problem_id=problem_id,
            revision=revision,
            cases=cases,
        )

    async def get_latest(
        self,
        problem_id: UUID,
    ) -> TestCaseSet | None:
        document = await self._collection.find_one(
            {
                "problem_id": problem_id,
            },
            {
                "_id": 0,
                "revision": 1,
            },
            sort=[("revision", DESCENDING)],
        )

        if document is None:
            return None

        revision = document.get("revision")
        if not isinstance(revision, int):
            raise ValueError("stored test case contains an invalid revision")

        return await self.get_by_revision(
            problem_id=problem_id,
            revision=revision,
        )
