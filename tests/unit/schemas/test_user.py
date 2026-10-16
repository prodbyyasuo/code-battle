from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.enums import UserRole
from app.schemas import UserRead, UserRegister


def test_user_register_accepts_valid_data() -> None:
    schema = UserRegister(
        email="user@example.com",
        username="code_master",
        password="strong-password",
    )

    assert schema.email == "user@example.com"
    assert schema.username == "code_master"
    assert schema.password.get_secret_value() == "strong-password"


def test_user_register_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserRegister(
            email="user@example.com",
            username="code_master",
            password="short",
        )


def test_user_register_rejects_invalid_username() -> None:
    with pytest.raises(ValidationError):
        UserRegister(
            email="user@example.com",
            username="invalid username",
            password="strong-password",
        )


def test_user_register_does_not_accept_role() -> None:
    with pytest.raises(ValidationError):
        UserRegister.model_validate(
            {
                "email": "user@example.com",
                "username": "code_master",
                "password": "strong-password",
                "role": "admin",
            }
        )


def test_user_read_does_not_expose_password_hash() -> None:
    now = datetime.now(UTC)

    schema = UserRead.model_validate(
        {
            "id": uuid4(),
            "email": "user@example.com",
            "username": "code_master",
            "role": UserRole.USER,
            "rating": 0,
            "is_active": True,
            "is_verified": False,
            "created_at": now,
            "updated_at": now,
        }
    )

    assert "password" not in schema.model_dump()
    assert "password_hash" not in schema.model_dump()
