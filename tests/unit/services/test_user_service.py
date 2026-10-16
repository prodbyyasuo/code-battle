from datetime import datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import verify_password
from app.core.tokens import TokenService
from app.domain import TokenType, UserRole
from app.integrations import EmailDispatcher, OneTimeTokenStore
from app.models import User
from app.repositories import UserRepository
from app.schemas import UserLogin, UserRegister
from app.services import AuthenticationError, UserService


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    async def create(
        self,
        *,
        email: str,
        username: str,
        password_hash: str,
    ) -> User:
        now = datetime.now().astimezone()
        user = User(
            id=uuid4(),
            email=email.lower(),
            username=username,
            password_hash=password_hash,
            role=UserRole.USER,
            rating=0,
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        self.users[user.id] = user
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        normalized = email.lower()
        return next(
            (
                user
                for user in self.users.values()
                if user.email.lower() == normalized
            ),
            None,
        )

    async def get_by_username(self, username: str) -> User | None:
        normalized = username.lower()
        return next(
            (
                user
                for user in self.users.values()
                if user.username.lower() == normalized
            ),
            None,
        )

    async def mark_verified(self, user_id: UUID) -> User | None:
        user = self.users.get(user_id)
        if user is not None:
            user.is_verified = True
        return user

    async def update_password(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> User | None:
        user = self.users.get(user_id)
        if user is not None:
            user.password_hash = password_hash
        return user


class FakeTokenStore:
    def __init__(self) -> None:
        self.consumed: set[UUID] = set()

    async def consume(
        self,
        *,
        token_type: TokenType,
        jti: UUID,
        expires_at: datetime,
    ) -> bool:
        del token_type, expires_at
        if jti in self.consumed:
            return False
        self.consumed.add(jti)
        return True


class FakeEmailDispatcher:
    def __init__(self) -> None:
        self.verifications: list[tuple[str, str]] = []
        self.password_resets: list[tuple[str, str]] = []

    async def send_verification(self, email: str, token: str) -> None:
        self.verifications.append((email, token))

    async def send_password_reset(self, email: str, token: str) -> None:
        self.password_resets.append((email, token))


@pytest.fixture
def service_parts() -> tuple[
    UserService,
    FakeSession,
    FakeUserRepository,
    FakeTokenStore,
    FakeEmailDispatcher,
    TokenService,
]:
    session = FakeSession()
    users = FakeUserRepository()
    token_store = FakeTokenStore()
    email = FakeEmailDispatcher()
    tokens = TokenService(get_settings())
    service = UserService(
        session=cast(AsyncSession, session),
        users=cast(UserRepository, users),
        tokens=tokens,
        token_store=cast(OneTimeTokenStore, token_store),
        email_dispatcher=cast(EmailDispatcher, email),
    )
    return service, session, users, token_store, email, tokens


async def register_user(service: UserService) -> User:
    return await service.register(
        UserRegister(
            email="user@example.com",
            username="code_master",
            password="correct-password",
        )
    )


async def test_register_hashes_password_and_queues_verification(
    service_parts: tuple[
        UserService,
        FakeSession,
        FakeUserRepository,
        FakeTokenStore,
        FakeEmailDispatcher,
        TokenService,
    ],
) -> None:
    service, session, _, _, email, tokens = service_parts

    user = await register_user(service)

    assert session.commits == 1
    assert await verify_password(
        "correct-password",
        user.password_hash,
    )
    recipient, token = email.verifications[0]
    assert recipient == user.email
    assert (
        tokens.decode(
            token,
            expected_type=TokenType.EMAIL_VERIFICATION,
        ).subject
        == user.id
    )


async def test_login_issues_access_and_refresh_tokens(
    service_parts: tuple[
        UserService,
        FakeSession,
        FakeUserRepository,
        FakeTokenStore,
        FakeEmailDispatcher,
        TokenService,
    ],
) -> None:
    service, _, _, _, _, tokens = service_parts
    user = await register_user(service)

    pair = await service.login(
        UserLogin(
            email=user.email,
            password="correct-password",
        )
    )

    assert (
        tokens.decode(
            pair.access_token,
            expected_type=TokenType.ACCESS,
        ).subject
        == user.id
    )
    assert (
        tokens.decode(
            pair.refresh_token,
            expected_type=TokenType.REFRESH,
        ).subject
        == user.id
    )


async def test_wrong_password_is_rejected(
    service_parts: tuple[
        UserService,
        FakeSession,
        FakeUserRepository,
        FakeTokenStore,
        FakeEmailDispatcher,
        TokenService,
    ],
) -> None:
    service = service_parts[0]
    await register_user(service)

    with pytest.raises(AuthenticationError):
        await service.login(
            UserLogin(
                email="user@example.com",
                password="wrong-password",
            )
        )


async def test_refresh_token_is_rotated_only_once(
    service_parts: tuple[
        UserService,
        FakeSession,
        FakeUserRepository,
        FakeTokenStore,
        FakeEmailDispatcher,
        TokenService,
    ],
) -> None:
    service = service_parts[0]
    user = await register_user(service)
    pair = await service.login(
        UserLogin(
            email=user.email,
            password="correct-password",
        )
    )

    rotated = await service.refresh(pair.refresh_token)

    assert rotated.refresh_token != pair.refresh_token
    with pytest.raises(AuthenticationError):
        await service.refresh(pair.refresh_token)


async def test_refresh_token_cannot_authenticate_me(
    service_parts: tuple[
        UserService,
        FakeSession,
        FakeUserRepository,
        FakeTokenStore,
        FakeEmailDispatcher,
        TokenService,
    ],
) -> None:
    service = service_parts[0]
    user = await register_user(service)
    pair = await service.login(
        UserLogin(
            email=user.email,
            password="correct-password",
        )
    )

    with pytest.raises(AuthenticationError):
        await service.get_current_user(pair.refresh_token)


async def test_email_verification_token_is_one_time(
    service_parts: tuple[
        UserService,
        FakeSession,
        FakeUserRepository,
        FakeTokenStore,
        FakeEmailDispatcher,
        TokenService,
    ],
) -> None:
    service, _, _, _, email, _ = service_parts
    await register_user(service)
    token = email.verifications[0][1]

    verified = await service.verify_email(token)

    assert verified.is_verified is True
    with pytest.raises(AuthenticationError):
        await service.verify_email(token)


async def test_password_reset_changes_hash_and_token_is_one_time(
    service_parts: tuple[
        UserService,
        FakeSession,
        FakeUserRepository,
        FakeTokenStore,
        FakeEmailDispatcher,
        TokenService,
    ],
) -> None:
    service, _, _, _, email, _ = service_parts
    user = await register_user(service)
    await service.request_password_reset(user.email)
    token = email.password_resets[0][1]

    await service.reset_password(
        token=token,
        new_password="new-correct-password",
    )

    assert await verify_password(
        "new-correct-password",
        user.password_hash,
    )
    with pytest.raises(AuthenticationError):
        await service.reset_password(
            token=token,
            new_password="another-password",
        )


async def test_missing_email_requests_are_neutral_noops(
    service_parts: tuple[
        UserService,
        FakeSession,
        FakeUserRepository,
        FakeTokenStore,
        FakeEmailDispatcher,
        TokenService,
    ],
) -> None:
    service, _, _, _, email, _ = service_parts

    await service.request_email_verification("missing@example.com")
    await service.request_password_reset("missing@example.com")

    assert email.verifications == []
    assert email.password_resets == []
