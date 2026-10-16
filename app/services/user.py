"""User registration, authentication, and account lifecycle use cases."""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    hash_password,
    verify_password,
)
from app.core.tokens import InvalidTokenError, TokenPayload, TokenService
from app.domain import TokenType
from app.integrations import EmailDispatcher, OneTimeTokenStore
from app.models import User
from app.repositories import UserAlreadyExistsError, UserRepository
from app.schemas import TokenPair, UserLogin, UserRegister
from app.services.exceptions import AuthenticationError, UserNotFoundError

logger = logging.getLogger(__name__)


class UserService:
    """Coordinate user persistence, JWTs, Redis, and email jobs."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        users: UserRepository,
        tokens: TokenService,
        token_store: OneTimeTokenStore,
        email_dispatcher: EmailDispatcher,
    ) -> None:
        self._session = session
        self._users = users
        self._tokens = tokens
        self._token_store = token_store
        self._email_dispatcher = email_dispatcher

    async def register(self, data: UserRegister) -> User:
        """Register a user and queue email verification."""
        if await self._users.get_by_email(str(data.email)) is not None:
            raise UserAlreadyExistsError("email")
        if await self._users.get_by_username(data.username) is not None:
            raise UserAlreadyExistsError("username")

        password_hash = await hash_password(data.password.get_secret_value())
        try:
            user = await self._users.create(
                email=str(data.email),
                username=data.username,
                password_hash=password_hash,
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        token = self._tokens.create_email_verification_token(user.id)
        await self._dispatch_verification(user.email, token)
        return user

    async def login(self, data: UserLogin) -> TokenPair:
        """Validate credentials and issue an access/refresh pair."""
        user = await self._users.get_by_email(str(data.email))
        candidate_hash = (
            user.password_hash if user is not None else DUMMY_PASSWORD_HASH
        )
        password_matches = await verify_password(
            data.password.get_secret_value(),
            candidate_hash,
        )
        if user is None or not password_matches or not user.is_active:
            raise AuthenticationError("Invalid email or password")

        return self._issue_pair(user.id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        """Rotate a refresh token and reject every replay attempt."""
        payload = self._decode(
            refresh_token,
            expected_type=TokenType.REFRESH,
        )
        is_first_use = await self._token_store.consume(
            token_type=payload.token_type,
            jti=payload.jti,
            expires_at=payload.expires_at,
        )
        if not is_first_use:
            raise AuthenticationError("Refresh token has already been used")

        user = await self._users.get_by_id(payload.subject)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid refresh token")
        return self._issue_pair(user.id)

    async def get_current_user(self, access_token: str) -> User:
        """Resolve an active user from an access token."""
        payload = self._decode(
            access_token,
            expected_type=TokenType.ACCESS,
        )
        user = await self._users.get_by_id(payload.subject)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid access token")
        return user

    async def get_user(self, user_id: UUID) -> User:
        """Return one user for an authorized administrative operation."""
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    async def request_email_verification(self, email: str) -> None:
        """Queue verification only when an eligible account exists."""
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active or user.is_verified:
            return

        token = self._tokens.create_email_verification_token(user.id)
        await self._dispatch_verification(user.email, token)

    async def verify_email(self, token: str) -> User:
        """Consume a verification token and mark the account verified."""
        payload = self._decode(
            token,
            expected_type=TokenType.EMAIL_VERIFICATION,
        )
        await self._consume_action_token(payload)

        user = await self._users.mark_verified(payload.subject)
        if user is None or not user.is_active:
            await self._session.rollback()
            raise AuthenticationError("Invalid verification token")
        await self._commit()
        return user

    async def request_password_reset(self, email: str) -> None:
        """Queue reset instructions without revealing account existence."""
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            return

        token = self._tokens.create_password_reset_token(user.id)
        try:
            await self._email_dispatcher.send_password_reset(
                user.email,
                token,
            )
        except Exception:
            logger.exception(
                "Could not enqueue a password-reset email for user %s",
                user.id,
            )

    async def reset_password(
        self,
        *,
        token: str,
        new_password: str,
    ) -> None:
        """Consume a reset token and replace the stored Argon2 hash."""
        payload = self._decode(
            token,
            expected_type=TokenType.PASSWORD_RESET,
        )
        await self._consume_action_token(payload)
        password_hash = await hash_password(new_password)

        user = await self._users.update_password(
            payload.subject,
            password_hash,
        )
        if user is None or not user.is_active:
            await self._session.rollback()
            raise AuthenticationError("Invalid password-reset token")
        await self._commit()

    def _issue_pair(self, user_id: UUID) -> TokenPair:
        pair = self._tokens.create_pair(user_id)
        return TokenPair(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            expires_in=pair.access_expires_in,
        )

    def _decode(
        self,
        token: str,
        *,
        expected_type: TokenType,
    ) -> TokenPayload:
        try:
            return self._tokens.decode(
                token,
                expected_type=expected_type,
            )
        except InvalidTokenError as error:
            raise AuthenticationError("Invalid or expired token") from error

    async def _consume_action_token(self, payload: TokenPayload) -> None:
        consumed = await self._token_store.consume(
            token_type=payload.token_type,
            jti=payload.jti,
            expires_at=payload.expires_at,
        )
        if not consumed:
            raise AuthenticationError("Token has already been used")

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def _dispatch_verification(
        self,
        email: str,
        token: str,
    ) -> None:
        try:
            await self._email_dispatcher.send_verification(email, token)
        except Exception:
            logger.exception(
                "Could not enqueue an email-verification message for %s",
                email,
            )
