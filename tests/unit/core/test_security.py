from app.core.security import hash_password, verify_password


async def test_hash_password_creates_argon2_hash() -> None:
    password = "correct-password"

    password_hash = await hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


async def test_verify_password_accepts_correct_password() -> None:
    password = "correct-password"
    password_hash = await hash_password(password)

    assert await verify_password(password, password_hash) is True


async def test_verify_password_rejects_wrong_password() -> None:
    password_hash = await hash_password("correct-password")

    assert (
        await verify_password(
            "wrong-password",
            password_hash,
        )
        is False
    )


async def test_hash_password_uses_random_salt() -> None:
    first_hash = await hash_password("same-password")
    second_hash = await hash_password("same-password")

    assert first_hash != second_hash


async def test_verify_password_rejects_unknown_hash() -> None:
    assert (
        await verify_password(
            "password",
            "not-a-valid-hash",
        )
        is False
    )
