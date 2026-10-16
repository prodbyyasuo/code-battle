"""Integration tests for the SQLAlchemy user repository."""

from uuid import uuid4

import pytest

from app.domain import UserRole
from app.repositories import UserAlreadyExistsError
from app.repositories import UserRepository as RepositoryProtocol

pytestmark = pytest.mark.integration


def unique_credentials(prefix: str) -> tuple[str, str]:
    """Return credentials that cannot collide with existing local data."""
    suffix = uuid4().hex[:16]
    return (
        f"{prefix}-{suffix}@example.com",
        f"{prefix}_{suffix}",
    )


async def test_create_user(
    user_repository: RepositoryProtocol,
) -> None:
    email, username = unique_credentials("create")

    user = await user_repository.create(
        email=email.upper(),
        username=username,
        password_hash="argon2-hash",
    )

    assert user.id is not None
    assert user.email == email
    assert user.username == username
    assert user.password_hash == "argon2-hash"
    assert user.role is UserRole.USER
    assert user.rating == 0
    assert user.is_active is True
    assert user.is_verified is False
    assert user.created_at is not None
    assert user.updated_at is not None


async def test_get_user_by_id(
    user_repository: RepositoryProtocol,
) -> None:
    email, username = unique_credentials("by-id")
    created = await user_repository.create(
        email=email,
        username=username,
        password_hash="argon2-hash",
    )

    loaded = await user_repository.get_by_id(created.id)

    assert loaded is created


async def test_get_user_by_email_is_case_insensitive(
    user_repository: RepositoryProtocol,
) -> None:
    email, username = unique_credentials("by-email")
    created = await user_repository.create(
        email=email,
        username=username,
        password_hash="argon2-hash",
    )

    loaded = await user_repository.get_by_email(email.upper())

    assert loaded is created


async def test_get_user_by_username_is_case_insensitive(
    user_repository: RepositoryProtocol,
) -> None:
    email, username = unique_credentials("by-username")
    created = await user_repository.create(
        email=email,
        username=username.upper(),
        password_hash="argon2-hash",
    )

    loaded = await user_repository.get_by_username(username.lower())

    assert loaded is created


async def test_get_user_returns_none_when_missing(
    user_repository: RepositoryProtocol,
) -> None:
    suffix = uuid4().hex

    assert await user_repository.get_by_id(uuid4()) is None
    assert (
        await user_repository.get_by_email(f"missing-{suffix}@example.com")
        is None
    )
    assert await user_repository.get_by_username(f"missing_{suffix}") is None


async def test_mark_user_verified(
    user_repository: RepositoryProtocol,
) -> None:
    email, username = unique_credentials("verify")
    created = await user_repository.create(
        email=email,
        username=username,
        password_hash="argon2-hash",
    )

    updated = await user_repository.mark_verified(created.id)

    assert updated is not None
    assert updated.is_verified is True


async def test_update_password_hash(
    user_repository: RepositoryProtocol,
) -> None:
    email, username = unique_credentials("password")
    created = await user_repository.create(
        email=email,
        username=username,
        password_hash="old-hash",
    )

    updated = await user_repository.update_password(
        created.id,
        "new-hash",
    )

    assert updated is not None
    assert updated.password_hash == "new-hash"


async def test_create_rejects_duplicate_email(
    user_repository: RepositoryProtocol,
) -> None:
    email, first_username = unique_credentials("dup-email")
    _, second_username = unique_credentials("dup-email-2")

    await user_repository.create(
        email=email,
        username=first_username,
        password_hash="argon2-hash",
    )

    with pytest.raises(UserAlreadyExistsError) as error:
        await user_repository.create(
            email=email.upper(),
            username=second_username,
            password_hash="argon2-hash",
        )

    assert error.value.field == "email"


async def test_create_rejects_duplicate_username(
    user_repository: RepositoryProtocol,
) -> None:
    first_email, username = unique_credentials("dup-user")
    second_email, _ = unique_credentials("dup-user-2")

    await user_repository.create(
        email=first_email,
        username=username,
        password_hash="argon2-hash",
    )

    with pytest.raises(UserAlreadyExistsError) as error:
        await user_repository.create(
            email=second_email,
            username=username.upper(),
            password_hash="argon2-hash",
        )

    assert error.value.field == "username"
